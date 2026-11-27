from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.commerce_final.models import (
    CommerceExecution,
    InventoryCount,
    InventoryCountLine,
    Requisition,
    RequisitionLine,
    ReturnAuthorization,
    ShippingClaim,
)
from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase3a.models import PurchaseOrder, PurchaseOrderLine
from flowforge.phase3b.models import (
    InventoryBalance,
    InventoryMovement,
    InventoryReservation,
    SalesOrder,
    SalesOrderLine,
    Shipment,
)

from .models import CommerceEvent


class CompletionService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def idem(self, op, key, typ, id):
        old = await self.db.scalar(
            select(CommerceExecution).where(
                CommerceExecution.tenant_id == self.ctx.tenant_id,
                CommerceExecution.operation == op,
                CommerceExecution.idempotency_key == key,
            )
        )
        if old:
            return old, True
        x = CommerceExecution(
            tenant_id=self.ctx.tenant_id,
            operation=op,
            idempotency_key=key,
            aggregate_type=typ,
            aggregate_id=id,
        )
        self.db.add(x)
        return x, False

    async def event(self, t, a, id, p):
        self.db.add(
            CommerceEvent(
                tenant_id=self.ctx.tenant_id,
                event_type=t,
                aggregate_type=a,
                aggregate_id=id,
                payload_json=json.dumps(p, default=str),
            )
        )

    async def requisition_to_po(self, rid, b):
        r = await self.db.scalar(
            select(Requisition)
            .where(Requisition.id == rid, Requisition.tenant_id == self.ctx.tenant_id)
            .with_for_update()
        )
        if not r or r.status != "approved":
            raise ValueError("Approved requisition required")
        _, dup = await self.idem("requisition_to_po", b.idempotency_key, "requisition", rid)
        if dup:
            return {"idempotent": True}
        lines = list(
            (
                await self.db.scalars(
                    select(RequisitionLine).where(
                        RequisitionLine.requisition_id == rid,
                        RequisitionLine.tenant_id == self.ctx.tenant_id,
                    )
                )
            ).all()
        )
        po = PurchaseOrder(
            tenant_id=self.ctx.tenant_id,
            po_number=f"PO-{r.number}",
            vendor_id=b.vendor_id,
            currency_code=b.currency_code,
            status="draft",
            created_by=self.ctx.user_id,
            total_amount=r.total_amount,
        )
        self.db.add(po)
        await self.db.flush()
        for i, l in enumerate(lines, 1):
            self.db.add(
                PurchaseOrderLine(
                    tenant_id=self.ctx.tenant_id,
                    purchase_order_id=po.id,
                    line_number=i,
                    description=l.description,
                    quantity=l.quantity,
                    unit_price=l.unit_price,
                    expense_account_id=None,
                    received_quantity=0,
                    invoiced_quantity=0,
                )
            )
        r.status = "converted"
        r.converted_po_id = po.id
        await self.event("procurement.po_created", "purchase_order", po.id, {"requisition_id": rid})
        await self.db.commit()
        return {"purchase_order_id": str(po.id)}

    async def reserve(self, b):
        line = await self.db.scalar(
            select(SalesOrderLine).where(
                SalesOrderLine.id == b.order_line_id, SalesOrderLine.tenant_id == self.ctx.tenant_id
            )
        )
        if not line:
            raise LookupError("Order line not found")
        bal = await self.db.scalar(
            select(InventoryBalance)
            .where(
                InventoryBalance.tenant_id == self.ctx.tenant_id,
                InventoryBalance.product_id == line.product_id,
                InventoryBalance.warehouse_id == b.warehouse_id,
            )
            .with_for_update()
        )
        if not bal or bal.on_hand - bal.reserved - bal.allocated < b.quantity:
            raise ValueError("Insufficient available inventory")
        _, dup = await self.idem("reserve", b.idempotency_key, "sales_order_line", line.id)
        if dup:
            return {"idempotent": True}
        bal.reserved += b.quantity
        line.reserved_quantity += b.quantity
        res = InventoryReservation(
            tenant_id=self.ctx.tenant_id,
            order_line_id=line.id,
            balance_id=bal.id,
            quantity=b.quantity,
            status="active",
        )
        self.db.add(res)
        await self.db.commit()
        return res

    async def approve_count(self, cid, key):
        c = await self.db.scalar(
            select(InventoryCount)
            .where(InventoryCount.id == cid, InventoryCount.tenant_id == self.ctx.tenant_id)
            .with_for_update()
        )
        if not c or c.status != "open":
            raise ValueError("Open count required")
        _, dup = await self.idem("inventory_count", key, "inventory_count", cid)
        if dup:
            return {"idempotent": True}
        lines = list(
            (
                await self.db.scalars(
                    select(InventoryCountLine).where(
                        InventoryCountLine.count_id == cid,
                        InventoryCountLine.tenant_id == self.ctx.tenant_id,
                    )
                )
            ).all()
        )
        for l in lines:
            bal = await self.db.scalar(
                select(InventoryBalance)
                .where(
                    InventoryBalance.tenant_id == self.ctx.tenant_id,
                    InventoryBalance.product_id == l.product_id,
                    InventoryBalance.warehouse_id == c.warehouse_id,
                    InventoryBalance.location_id == l.location_id,
                )
                .with_for_update()
            )
            if not bal:
                raise LookupError("Count balance not found")
            bal.on_hand = l.counted_quantity
            self.db.add(
                InventoryMovement(
                    tenant_id=self.ctx.tenant_id,
                    product_id=l.product_id,
                    warehouse_id=c.warehouse_id,
                    location_id=l.location_id,
                    movement_type="count_adjustment",
                    quantity=l.variance,
                    unit_cost=0,
                    idempotency_key=f"{key}-{l.id}",
                )
            )
        c.status = "approved"
        c.approved_by = self.ctx.user_id
        await self.db.commit()
        return c

    async def fulfill(self, b):
        order = await self.db.scalar(
            select(SalesOrder).where(
                SalesOrder.id == b.order_id, SalesOrder.tenant_id == self.ctx.tenant_id
            )
        )
        if not order:
            raise LookupError("Order not found")
        _, dup = await self.idem("fulfill", b.idempotency_key, "sales_order", order.id)
        if dup:
            return {"idempotent": True}
        lines = list(
            (
                await self.db.scalars(
                    select(SalesOrderLine).where(
                        SalesOrderLine.order_id == order.id,
                        SalesOrderLine.tenant_id == self.ctx.tenant_id,
                    )
                )
            ).all()
        )
        for l in lines:
            qty = l.reserved_quantity - l.shipped_quantity
            if qty <= 0:
                continue
            bal = await self.db.scalar(
                select(InventoryBalance)
                .where(
                    InventoryBalance.tenant_id == self.ctx.tenant_id,
                    InventoryBalance.product_id == l.product_id,
                    InventoryBalance.warehouse_id == b.warehouse_id,
                )
                .with_for_update()
            )
            if not bal or bal.on_hand < qty:
                raise ValueError("Insufficient inventory for fulfillment")
            bal.on_hand -= qty
            bal.reserved = max(Decimal("0"), bal.reserved - qty)
            l.shipped_quantity += qty
            self.db.add(
                InventoryMovement(
                    tenant_id=self.ctx.tenant_id,
                    product_id=l.product_id,
                    warehouse_id=b.warehouse_id,
                    location_id=bal.location_id,
                    movement_type="shipment",
                    quantity=-qty,
                    unit_cost=0,
                    idempotency_key=f"{b.idempotency_key}-{l.id}",
                )
            )
        ship = Shipment(
            tenant_id=self.ctx.tenant_id,
            order_id=order.id,
            shipment_number=b.shipment_number,
            ship_date=datetime.now(UTC).date(),
            status="shipped",
        )
        self.db.add(ship)
        order.status = "shipped"
        await self.event("fulfillment.shipped", "shipment", ship.id, {"order_id": order.id})
        await self.db.commit()
        return ship

    async def receive_return(self, rid, b):
        r = await self.db.scalar(
            select(ReturnAuthorization).where(
                ReturnAuthorization.id == rid, ReturnAuthorization.tenant_id == self.ctx.tenant_id
            )
        )
        if not r or r.status != "approved":
            raise ValueError("Approved return required")
        _, dup = await self.idem("return_receive", b.idempotency_key, "return", rid)
        if dup:
            return {"idempotent": True}
        r.status = "received"
        r.received_at = datetime.now(UTC)
        await self.event("return.received", "return", rid, {"warehouse_id": b.warehouse_id})
        await self.db.commit()
        return r

    async def claim_action(self, id, target):
        c = await self.db.scalar(
            select(ShippingClaim).where(
                ShippingClaim.id == id, ShippingClaim.tenant_id == self.ctx.tenant_id
            )
        )
        if not c:
            raise LookupError("Claim not found")
        allowed = {
            "draft": {"submitted"},
            "submitted": {"approved", "rejected"},
            "approved": {"paid", "closed"},
            "paid": {"closed"},
        }
        if target not in allowed.get(c.status, set()):
            raise ValueError("Invalid claim transition")
        c.status = target
        await self.db.commit()
        return c

    async def valuation(self):
        rows = (
            await self.db.execute(
                select(
                    InventoryBalance.product_id,
                    func.coalesce(func.sum(InventoryBalance.on_hand), 0),
                )
                .where(InventoryBalance.tenant_id == self.ctx.tenant_id)
                .group_by(InventoryBalance.product_id)
            )
        ).all()
        return [{"product_id": str(p), "on_hand": q} for p, q in rows]

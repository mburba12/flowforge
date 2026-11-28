from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase3b.models import (
    InventoryBalance,
    InventoryMovement,
    WarehouseLocation,
)
from flowforge.platform.services import record_change

from .models import *  # noqa: F403, F405


class CommerceService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def save(self, o, e):
        self.db.add(o)
        await self.db.flush()
        await record_change(self.db, self.ctx.tenant_id, self.ctx.user_id, "created", e, str(o.id))
        await self.db.commit()
        await self.db.refresh(o)
        return o

    async def requisition(self, b):
        r = Requisition(
            tenant_id=self.ctx.tenant_id,
            number=b.number,
            needed_on=b.needed_on,
            requester_id=self.ctx.user_id,
        )
        self.db.add(r)
        await self.db.flush()
        total = Decimal("0")
        for line in b.lines:
            t = line.quantity * line.unit_price
            total += t
            self.db.add(
                RequisitionLine(
                    tenant_id=self.ctx.tenant_id,
                    requisition_id=r.id,
                    line_total=t,
                    **line.model_dump(),
                )
            )
        r.total_amount = total
        await self.db.commit()
        return r

    async def requisition_action(self, id, target):
        r = await self._get(Requisition, id)
        allowed = {
            "draft": {"submitted", "cancelled"},
            "submitted": {"approved", "rejected"},
            "approved": {"converted"},
        }
        if target not in allowed.get(r.status, set()):
            raise ValueError("Invalid requisition transition")
        if target == "approved":
            r.approved_by = self.ctx.user_id
        r.status = target
        await self.db.commit()
        return r

    async def transfer(self, b):
        return await self.save(
            InventoryTransfer(tenant_id=self.ctx.tenant_id, **b.model_dump()), "inventory_transfer"
        )

    async def transfer_action(self, id, target, key):
        x = await self._get(InventoryTransfer, id)
        old = await self._execution("transfer", key, x.id)
        if old:
            return old
        if target not in {"approved", "completed", "cancelled"}:
            raise ValueError("Invalid transfer action")
        if target == "approved":
            x.approved_by = self.ctx.user_id
        if target == "completed":
            if x.status != "approved":
                raise ValueError("Transfer must be approved")
            await self._move(x.product_id, x.source_warehouse_id, -x.quantity, key + "-out")
            await self._move(x.product_id, x.target_warehouse_id, x.quantity, key + "-in")
        x.status = target
        await self.db.commit()
        await self.db.refresh(x)
        return x

    async def _move(self, pid, wid, qty, key):
        bal = await self.db.scalar(
            select(InventoryBalance)
            .where(
                InventoryBalance.tenant_id == self.ctx.tenant_id,
                InventoryBalance.product_id == pid,
                InventoryBalance.warehouse_id == wid,
            )
            .with_for_update()
        )
        if not bal and qty > 0:
            # First stock in this warehouse: open a balance at its first location.
            location = await self.db.scalar(
                select(WarehouseLocation.id)
                .where(
                    WarehouseLocation.tenant_id == self.ctx.tenant_id,
                    WarehouseLocation.warehouse_id == wid,
                )
                .order_by(WarehouseLocation.code)
                .limit(1)
            )
            if location is None:
                raise ValueError("The target warehouse has no location to receive stock")
            bal = InventoryBalance(
                tenant_id=self.ctx.tenant_id,
                product_id=pid,
                warehouse_id=wid,
                location_id=location,
                on_hand=0,
                reserved=0,
                allocated=0,
            )
            self.db.add(bal)
            await self.db.flush()
        if not bal:
            raise LookupError("Inventory balance not found")
        if bal.on_hand + qty < 0:
            raise ValueError("Insufficient inventory")
        bal.on_hand += qty
        self.db.add(
            InventoryMovement(
                tenant_id=self.ctx.tenant_id,
                product_id=pid,
                warehouse_id=wid,
                location_id=bal.location_id,
                movement_type="transfer",
                quantity=qty,
                unit_cost=0,
                idempotency_key=key,
            )
        )

    async def count(self, b):
        return await self.save(
            InventoryCount(
                tenant_id=self.ctx.tenant_id,
                number=b.number,
                warehouse_id=b.warehouse_id,
                counted_by=self.ctx.user_id,
            ),
            "inventory_count",
        )

    async def count_line(self, cid, b):
        return await self.save(
            InventoryCountLine(
                tenant_id=self.ctx.tenant_id,
                count_id=cid,
                variance=b.counted_quantity - b.system_quantity,
                **b.model_dump(),
            ),
            "inventory_count_line",
        )

    async def return_create(self, b):
        return await self.save(
            ReturnAuthorization(tenant_id=self.ctx.tenant_id, **b.model_dump()),
            "return_authorization",
        )

    async def return_action(self, id, target):
        x = await self._get(ReturnAuthorization, id)
        allowed = {
            "requested": {"approved", "rejected"},
            "approved": {"received", "cancelled"},
            "received": {"refunded", "closed"},
        }
        if target not in allowed.get(x.status, set()):
            raise ValueError("Invalid return transition")
        x.status = target
        if target == "received":
            x.received_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(x)
        return x

    async def label(self, b):
        old = await self.db.scalar(
            select(ShippingLabel).where(
                ShippingLabel.tenant_id == self.ctx.tenant_id,
                ShippingLabel.idempotency_key == b.idempotency_key,
            )
        )
        if old:
            return old
        return await self.save(
            ShippingLabel(
                tenant_id=self.ctx.tenant_id,
                status="simulated",
                tracking_number_mask="SIMULATED",
                **b.model_dump(),
            ),
            "shipping_label",
        )

    async def claim(self, b):
        return await self.save(
            ShippingClaim(
                tenant_id=self.ctx.tenant_id,
                evidence_json=json.dumps(b.evidence),
                **b.model_dump(exclude={"evidence"}),
            ),
            "shipping_claim",
        )

    async def _get(self, m, id):
        x = await self.db.scalar(select(m).where(m.id == id, m.tenant_id == self.ctx.tenant_id))
        if not x:
            raise LookupError("Record not found")
        return x

    async def _execution(self, op, key, id):
        old = await self.db.scalar(
            select(CommerceExecution).where(
                CommerceExecution.tenant_id == self.ctx.tenant_id,
                CommerceExecution.operation == op,
                CommerceExecution.idempotency_key == key,
            )
        )
        if old:
            return old
        self.db.add(
            CommerceExecution(
                tenant_id=self.ctx.tenant_id,
                operation=op,
                idempotency_key=key,
                aggregate_type=op,
                aggregate_id=id,
            )
        )
        return None

    async def list(self, m):
        return list(
            (await self.db.scalars(select(m).where(m.tenant_id == self.ctx.tenant_id))).all()
        )

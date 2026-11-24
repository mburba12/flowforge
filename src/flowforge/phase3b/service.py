from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase2b.models import JournalEntry, JournalLine

from .models import (
    AROpenItem,
    CustomerInvoice,
    CustomerProfile,
    CustomerReceipt,
    InventoryBalance,
    InventoryMovement,
    InventoryReservation,
    Product,
    ReceiptAllocation,
    SalesOrder,
    SalesOrderLine,
    Shipment,
    UnitOfMeasure,
    Warehouse,
    WarehouseLocation,
)
from .schemas import (
    CustomerCreate,
    InventoryAdjust,
    LocationCreate,
    OrderCreate,
    ProductCreate,
    ReceiptCreate,
    WarehouseCreate,
)


class Phase3BError(Exception):
    pass


class CommerceService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def customer(self, d: CustomerCreate) -> CustomerProfile:
        n = await self.db.scalar(
            select(func.count())
            .select_from(CustomerProfile)
            .where(CustomerProfile.tenant_id == self.tenant_id)
        )
        x = CustomerProfile(
            tenant_id=self.tenant_id, customer_number=f"C-{int(n or 0) + 1:08d}", **d.model_dump()
        )
        self.db.add(x)
        await self.db.commit()
        await self.db.refresh(x)
        return x

    async def product(self, d: ProductCreate) -> Product:
        if await self.db.get(UnitOfMeasure, d.base_uom) is None:
            self.db.add(UnitOfMeasure(code=d.base_uom, name=d.base_uom))
        x = Product(tenant_id=self.tenant_id, **d.model_dump())
        self.db.add(x)
        await self.db.commit()
        await self.db.refresh(x)
        return x

    async def warehouse(self, d: WarehouseCreate) -> Warehouse:
        x = Warehouse(tenant_id=self.tenant_id, **d.model_dump())
        self.db.add(x)
        await self.db.commit()
        await self.db.refresh(x)
        return x

    async def location(self, d: LocationCreate) -> WarehouseLocation:
        x = WarehouseLocation(tenant_id=self.tenant_id, **d.model_dump())
        self.db.add(x)
        await self.db.commit()
        await self.db.refresh(x)
        return x

    async def adjust(
        self,
        data: InventoryAdjust,
    ) -> InventoryBalance:
        duplicate_statement = select(InventoryMovement).where(
            InventoryMovement.tenant_id == self.tenant_id,
            InventoryMovement.idempotency_key == data.idempotency_key,
        )
        duplicate = await self.db.scalar(duplicate_statement)

        if duplicate is not None:
            raise Phase3BError("Duplicate idempotency key")

        balance_statement = (
            select(InventoryBalance)
            .where(
                InventoryBalance.tenant_id == self.tenant_id,
                InventoryBalance.product_id == data.product_id,
                InventoryBalance.location_id == data.location_id,
            )
            .with_for_update()
        )
        balance = await self.db.scalar(balance_statement)

        if balance is None:
            balance = InventoryBalance(
                tenant_id=self.tenant_id,
                product_id=data.product_id,
                warehouse_id=data.warehouse_id,
                location_id=data.location_id,
                on_hand=Decimal("0"),
                reserved=Decimal("0"),
                allocated=Decimal("0"),
            )
            self.db.add(balance)
            await self.db.flush()

        new_on_hand = balance.on_hand + data.quantity

        if new_on_hand < 0:
            raise Phase3BError("Insufficient inventory")

        balance.on_hand = new_on_hand

        movement_type = "adjustment_in" if data.quantity > 0 else "adjustment_out"

        self.db.add(
            InventoryMovement(
                tenant_id=self.tenant_id,
                product_id=data.product_id,
                warehouse_id=data.warehouse_id,
                location_id=data.location_id,
                movement_type=movement_type,
                quantity=abs(data.quantity),
                unit_cost=data.unit_cost,
                idempotency_key=data.idempotency_key,
            )
        )

        await self.db.commit()
        await self.db.refresh(balance)

        return balance

    async def order(
        self,
        data: OrderCreate,
    ) -> SalesOrder:
        customer_statement = select(CustomerProfile).where(
            CustomerProfile.id == data.customer_id,
            CustomerProfile.tenant_id == self.tenant_id,
        )
        customer = await self.db.scalar(customer_statement)

        if customer is None:
            raise Phase3BError("Customer profile was not found")

        total = sum(
            (line.quantity * line.unit_price for line in data.lines),
            Decimal("0"),
        )

        order_status = "credit_hold" if total > customer.credit_limit else "approved"

        count_statement = (
            select(func.count())
            .select_from(SalesOrder)
            .where(SalesOrder.tenant_id == self.tenant_id)
        )
        count = await self.db.scalar(count_statement)

        order = SalesOrder(
            tenant_id=self.tenant_id,
            order_number=(f"SO-{int(count or 0) + 1:08d}"),
            customer_id=data.customer_id,
            ledger_id=data.ledger_id,
            period_id=data.period_id,
            order_date=data.order_date,
            status=order_status,
            total_amount=total,
            created_by=self.user_id,
        )
        self.db.add(order)
        await self.db.flush()

        for line in data.lines:
            self.db.add(
                SalesOrderLine(
                    tenant_id=self.tenant_id,
                    order_id=order.id,
                    **line.model_dump(),
                )
            )

        await self.db.commit()
        await self.db.refresh(order)

        return order

    async def reserve(
        self,
        order_id: UUID,
    ) -> SalesOrder:
        order_statement = select(SalesOrder).where(
            SalesOrder.id == order_id,
            SalesOrder.tenant_id == self.tenant_id,
        )
        order = await self.db.scalar(order_statement)

        if order is None:
            raise Phase3BError("Order was not found")

        if order.status != "approved":
            raise Phase3BError("Order is not reservable")

        line_statement = select(SalesOrderLine).where(SalesOrderLine.order_id == order.id)
        lines = list((await self.db.scalars(line_statement)).all())

        if not lines:
            raise Phase3BError("Order has no lines")

        reservations: list[
            tuple[
                SalesOrderLine,
                InventoryBalance,
            ]
        ] = []

        for order_line in lines:
            balance_statement = (
                select(InventoryBalance)
                .where(
                    InventoryBalance.tenant_id == self.tenant_id,
                    InventoryBalance.product_id == order_line.product_id,
                )
                .with_for_update()
            )
            balance = await self.db.scalar(balance_statement)

            if balance is None:
                raise Phase3BError("Inventory balance was not found")

            available_quantity = balance.on_hand - balance.reserved - balance.allocated

            if available_quantity < order_line.quantity:
                raise Phase3BError("Insufficient available inventory")

            reservations.append(
                (
                    order_line,
                    balance,
                )
            )

        for order_line, balance in reservations:
            balance.reserved += order_line.quantity
            order_line.reserved_quantity = order_line.quantity

            self.db.add(
                InventoryReservation(
                    tenant_id=self.tenant_id,
                    order_line_id=order_line.id,
                    balance_id=balance.id,
                    quantity=order_line.quantity,
                )
            )

        order.status = "reserved"

        await self.db.commit()
        await self.db.refresh(order)

        return order

    async def ship_and_invoice(
        self, order_id: UUID, ship_date: date, due_date: date
    ) -> CustomerInvoice:
        o = await self.db.scalar(
            select(SalesOrder).where(
                SalesOrder.id == order_id, SalesOrder.tenant_id == self.tenant_id
            )
        )
        if o is None or o.status != "reserved":
            raise Phase3BError("Order is not ready to ship")
        customer = await self.db.get(CustomerProfile, o.customer_id)
        if customer is None:
            raise Phase3BError("Customer profile was not found")
        lines = list(
            (
                await self.db.scalars(select(SalesOrderLine).where(SalesOrderLine.order_id == o.id))
            ).all()
        )
        cost = Decimal("0")
        for line in lines:
            product = await self.db.get(Product, line.product_id)
            if product is None:
                raise Phase3BError("Product was not found")
            balance_statement = (
                select(InventoryBalance)
                .where(
                    InventoryBalance.tenant_id == self.tenant_id,
                    InventoryBalance.product_id == line.product_id,
                )
                .with_for_update()
            )
            balance = await self.db.scalar(balance_statement)

            if balance is None:
                raise Phase3BError("Inventory balance was not found")

            if balance.on_hand < line.quantity:
                raise Phase3BError("Insufficient on-hand inventory")

            if balance.reserved < line.quantity:
                raise Phase3BError("Reserved inventory is insufficient")

            balance.on_hand -= line.quantity
            balance.reserved -= line.quantity
            line.shipped_quantity = line.quantity
            cost += line.quantity * product.standard_cost
        shipment = Shipment(
            tenant_id=self.tenant_id,
            order_id=o.id,
            shipment_number=f"SH-{str(o.id)[:8]}",
            ship_date=ship_date,
        )
        self.db.add(shipment)
        cogs = JournalEntry(
            tenant_id=self.tenant_id,
            ledger_id=o.ledger_id,
            period_id=o.period_id,
            journal_number=f"COGS-{str(o.id)[:8]}",
            journal_date=ship_date,
            description="Shipment COGS",
            status="posted",
            created_by=self.user_id,
            approved_by=self.user_id,
            posted_at=datetime.now(UTC),
        )
        self.db.add(cogs)
        await self.db.flush()
        p = await self.db.get(Product, lines[0].product_id)
        if p is None:
            raise Phase3BError("Shipment product was not found")
        self.db.add_all(
            [
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=cogs.id,
                    line_number=1,
                    account_id=p.cogs_account_id,
                    debit=cost,
                    credit=0,
                    currency_code=customer.default_currency,
                ),
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=cogs.id,
                    line_number=2,
                    account_id=p.inventory_account_id,
                    debit=0,
                    credit=cost,
                    currency_code=customer.default_currency,
                ),
            ]
        )
        shipment.cogs_journal_id = cogs.id
        ar = JournalEntry(
            tenant_id=self.tenant_id,
            ledger_id=o.ledger_id,
            period_id=o.period_id,
            journal_number=f"AR-{str(o.id)[:8]}",
            journal_date=ship_date,
            description="Customer invoice",
            status="posted",
            created_by=self.user_id,
            approved_by=self.user_id,
            posted_at=datetime.now(UTC),
        )
        self.db.add(ar)
        await self.db.flush()
        self.db.add_all(
            [
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=ar.id,
                    line_number=1,
                    account_id=customer.ar_account_id,
                    debit=o.total_amount,
                    credit=0,
                    currency_code=customer.default_currency,
                ),
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=ar.id,
                    line_number=2,
                    account_id=customer.revenue_account_id,
                    debit=0,
                    credit=o.total_amount,
                    currency_code=customer.default_currency,
                ),
            ]
        )
        inv = CustomerInvoice(
            tenant_id=self.tenant_id,
            customer_id=customer.id,
            order_id=o.id,
            invoice_number=f"INV-{str(o.id)[:8]}",
            invoice_date=ship_date,
            due_date=due_date,
            total_amount=o.total_amount,
            journal_id=ar.id,
        )
        self.db.add(inv)
        await self.db.flush()
        self.db.add(
            AROpenItem(
                tenant_id=self.tenant_id,
                customer_id=customer.id,
                invoice_id=inv.id,
                original_amount=o.total_amount,
                open_amount=o.total_amount,
                due_date=due_date,
            )
        )
        o.status = "invoiced"
        await self.db.commit()
        await self.db.refresh(inv)
        return inv

    async def receipt(self, d: ReceiptCreate) -> CustomerReceipt:
        item = await self.db.scalar(
            select(AROpenItem).where(
                AROpenItem.id == d.open_item_id, AROpenItem.tenant_id == self.tenant_id
            )
        )
        if item is None or d.amount > item.open_amount:
            raise Phase3BError("Invalid receipt allocation")
        await self.db.get(CustomerProfile, item.customer_id)
        r = CustomerReceipt(
            tenant_id=self.tenant_id,
            customer_id=item.customer_id,
            receipt_date=d.receipt_date,
            amount=d.amount,
        )
        self.db.add(r)
        await self.db.flush()
        j = JournalEntry(
            tenant_id=self.tenant_id,
            ledger_id=d.ledger_id,
            period_id=d.period_id,
            journal_number=f"RCPT-{str(r.id)[:8]}",
            journal_date=d.receipt_date,
            description="Customer receipt",
            status="posted",
            created_by=self.user_id,
            approved_by=self.user_id,
            posted_at=datetime.now(UTC),
        )
        self.db.add(j)
        await self.db.flush()
        self.db.add_all(
            [
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=j.id,
                    line_number=1,
                    account_id=d.cash_account_id,
                    debit=d.amount,
                    credit=0,
                    currency_code=d.currency_code,
                ),
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=j.id,
                    line_number=2,
                    account_id=d.ar_account_id,
                    debit=0,
                    credit=d.amount,
                    currency_code=d.currency_code,
                ),
                ReceiptAllocation(
                    tenant_id=self.tenant_id, receipt_id=r.id, open_item_id=item.id, amount=d.amount
                ),
            ]
        )
        r.journal_id = j.id
        item.open_amount -= d.amount
        item.status = "paid" if item.open_amount == 0 else "partially_paid"
        await self.db.commit()
        await self.db.refresh(r)
        return r

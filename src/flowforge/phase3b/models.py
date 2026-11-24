from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id"))
    customer_number: Mapped[str] = mapped_column(String(50))
    default_currency: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    ar_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    revenue_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    credit_status: Mapped[str] = mapped_column(String(30), default="approved")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UnitOfMeasure(Base):
    __tablename__ = "units_of_measure"
    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    precision: Mapped[int] = mapped_column(Integer, default=4)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_product_sku"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    sku: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(200))
    base_uom: Mapped[str] = mapped_column(ForeignKey("units_of_measure.code"))
    sales_price: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    standard_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    inventory_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    cogs_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    allow_negative: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Warehouse(Base):
    __tablename__ = "warehouses"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(150))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WarehouseLocation(Base):
    __tablename__ = "warehouse_locations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(50))
    location_type: Mapped[str] = mapped_column(String(30), default="standard")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "location_id", name="uq_inventory_balance"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey("warehouses.id"))
    location_id: Mapped[UUID] = mapped_column(ForeignKey("warehouse_locations.id"))
    on_hand: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    reserved: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    allocated: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_inventory_idempotency"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey("warehouses.id"))
    location_id: Mapped[UUID] = mapped_column(ForeignKey("warehouse_locations.id"))
    movement_type: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_number: Mapped[str] = mapped_column(String(50))
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customer_profiles.id"))
    ledger_id: Mapped[UUID] = mapped_column(ForeignKey("ledgers.id"))
    period_id: Mapped[UUID] = mapped_column(ForeignKey("accounting_periods.id"))
    order_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class SalesOrderLine(Base):
    __tablename__ = "sales_order_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(ForeignKey("sales_orders.id", ondelete="CASCADE"))
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    shipped_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    invoiced_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_line_id: Mapped[UUID] = mapped_column(ForeignKey("sales_order_lines.id"))
    balance_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_balances.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    status: Mapped[str] = mapped_column(String(30), default="reserved")


class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(ForeignKey("sales_orders.id"))
    shipment_number: Mapped[str] = mapped_column(String(50))
    ship_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="shipped")
    cogs_journal_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))


class CustomerInvoice(Base):
    __tablename__ = "customer_invoices"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customer_profiles.id"))
    order_id: Mapped[UUID] = mapped_column(ForeignKey("sales_orders.id"))
    invoice_number: Mapped[str] = mapped_column(String(50))
    invoice_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30), default="posted")
    journal_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))


class AROpenItem(Base):
    __tablename__ = "ar_open_items"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customer_profiles.id"))
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("customer_invoices.id"))
    original_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    open_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="open")


class CustomerReceipt(Base):
    __tablename__ = "customer_receipts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customer_profiles.id"))
    receipt_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30), default="applied")
    journal_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))


class ReceiptAllocation(Base):
    __tablename__ = "receipt_allocations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    receipt_id: Mapped[UUID] = mapped_column(ForeignKey("customer_receipts.id", ondelete="CASCADE"))
    open_item_id: Mapped[UUID] = mapped_column(ForeignKey("ar_open_items.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))

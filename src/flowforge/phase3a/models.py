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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class VendorProfile(Base):
    __tablename__ = "vendor_profiles"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    vendor_number: Mapped[str] = mapped_column(String(50))
    default_currency: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    payment_terms_id: Mapped[UUID | None] = mapped_column(ForeignKey("payment_terms.id"))
    ap_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    payment_hold: Mapped[bool] = mapped_column(Boolean, default=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (UniqueConstraint("tenant_id", "po_number", name="uq_purchase_order_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    po_number: Mapped[str] = mapped_column(String(50))
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("vendor_profiles.id"))
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    order_date: Mapped[date] = mapped_column(Date)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True
    )
    line_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    expense_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    invoiced_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    receipt_number: Mapped[str] = mapped_column(String(50))
    purchase_order_id: Mapped[UUID] = mapped_column(ForeignKey("purchase_orders.id"))
    status: Mapped[str] = mapped_column(String(30), default="posted")
    receipt_date: Mapped[date] = mapped_column(Date)
    received_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    receipt_id: Mapped[UUID] = mapped_column(ForeignKey("goods_receipts.id", ondelete="CASCADE"))
    po_line_id: Mapped[UUID] = mapped_column(ForeignKey("purchase_order_lines.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))


class VendorInvoice(Base):
    __tablename__ = "vendor_invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "vendor_id", "invoice_number", name="uq_vendor_invoice"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("vendor_profiles.id"))
    purchase_order_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_orders.id"))
    invoice_number: Mapped[str] = mapped_column(String(100))
    invoice_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    status: Mapped[str] = mapped_column(String(30), default="captured")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    posted_journal_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))


class VendorInvoiceLine(Base):
    __tablename__ = "vendor_invoice_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("vendor_invoices.id", ondelete="CASCADE"))
    po_line_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_order_lines.id"))
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))


class MatchPolicy(Base):
    __tablename__ = "ap_match_policies"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    quantity_tolerance_bps: Mapped[int] = mapped_column(Integer, default=0)
    price_tolerance_bps: Mapped[int] = mapped_column(Integer, default=100)
    line_value_tolerance: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=5)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class InvoiceMatch(Base):
    __tablename__ = "invoice_matches"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("vendor_invoices.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(40))
    exception_count: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[str] = mapped_column(Text, default="")


class APOpenItem(Base):
    __tablename__ = "ap_open_items"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("vendor_profiles.id"))
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("vendor_invoices.id"))
    original_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    open_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="open")

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class VendorPayment(Base):
    __tablename__ = "vendor_payments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("vendor_profiles.id"))
    payment_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30), default="posted")
    journal_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))


class VendorPaymentAllocation(Base):
    __tablename__ = "vendor_payment_allocations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("vendor_payments.id", ondelete="CASCADE"))
    open_item_id: Mapped[UUID] = mapped_column(ForeignKey("ap_open_items.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))


class APReconciliationRun(Base):
    __tablename__ = "ap_reconciliation_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ledger_id: Mapped[UUID] = mapped_column(ForeignKey("ledgers.id"))
    period_id: Mapped[UUID] = mapped_column(ForeignKey("accounting_periods.id"))
    subledger_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    gl_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30))

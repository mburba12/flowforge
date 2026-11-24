from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class TaxLiability(Base):
    __tablename__ = "tax_liabilities"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    authority_id: Mapped[UUID] = mapped_column(ForeignKey("tax_authorities.id"))
    payroll_run_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_runs.id"))
    liability_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    open_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="open")


class TaxFilingCalendar(Base):
    __tablename__ = "tax_filing_calendars"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    authority_id: Mapped[UUID] = mapped_column(ForeignKey("tax_authorities.id"))
    frequency: Mapped[str] = mapped_column(String(30))
    active: Mapped[bool] = mapped_column(default=True)


class TaxReturn(Base):
    __tablename__ = "tax_returns"
    __table_args__ = (
        UniqueConstraint("tenant_id", "authority_id", "period_code", name="uq_tax_return_period"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    authority_id: Mapped[UUID] = mapped_column(ForeignKey("tax_authorities.id"))
    period_code: Mapped[str] = mapped_column(String(40))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    total_tax: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class TaxReturnLine(Base):
    __tablename__ = "tax_return_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    tax_return_id: Mapped[UUID] = mapped_column(ForeignKey("tax_returns.id", ondelete="CASCADE"))
    tax_code: Mapped[str] = mapped_column(String(50))
    taxable_wages: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))


class TaxRemittance(Base):
    __tablename__ = "tax_remittances"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    tax_return_id: Mapped[UUID] = mapped_column(ForeignKey("tax_returns.id"))
    payment_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30), default="posted")
    journal_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))


class TaxRemittanceAllocation(Base):
    __tablename__ = "tax_remittance_allocations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    remittance_id: Mapped[UUID] = mapped_column(
        ForeignKey("tax_remittances.id", ondelete="CASCADE")
    )
    liability_id: Mapped[UUID] = mapped_column(ForeignKey("tax_liabilities.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))


class TaxNotice(Base):
    __tablename__ = "tax_notices"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    authority_id: Mapped[UUID] = mapped_column(ForeignKey("tax_authorities.id"))
    notice_date: Mapped[date] = mapped_column(Date)
    reference: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="open")
    resolution: Mapped[str | None] = mapped_column(String(500))


class TaxReconciliationRun(Base):
    __tablename__ = "tax_reconciliation_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    authority_id: Mapped[UUID] = mapped_column(ForeignKey("tax_authorities.id"))
    subledger_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    gl_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30))

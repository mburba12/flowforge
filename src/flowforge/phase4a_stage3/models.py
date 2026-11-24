from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class PayrollRun(Base):
    __tablename__ = "payroll_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    pay_group_id: Mapped[UUID] = mapped_column(ForeignKey("pay_groups.id"))
    pay_period_id: Mapped[UUID] = mapped_column(ForeignKey("pay_periods.id"))
    ledger_id: Mapped[UUID] = mapped_column(ForeignKey("ledgers.id"))
    accounting_period_id: Mapped[UUID] = mapped_column(ForeignKey("accounting_periods.id"))
    run_number: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    posted_journal_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PayrollRunWorker(Base):
    __tablename__ = "payroll_run_workers"
    __table_args__ = (
        UniqueConstraint("payroll_run_id", "worker_id", name="uq_payroll_run_worker"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_run_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_runs.id", ondelete="CASCADE"))
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    gross_pay: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    pretax_deductions: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    employee_taxes: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    posttax_deductions: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    net_pay: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    employer_taxes: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)


class PayrollEarning(Base):
    __tablename__ = "payroll_earnings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_worker_id: Mapped[UUID] = mapped_column(
        ForeignKey("payroll_run_workers.id", ondelete="CASCADE")
    )
    earning_type: Mapped[str] = mapped_column(String(40))
    hours: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))


class PayrollDeduction(Base):
    __tablename__ = "payroll_deductions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_worker_id: Mapped[UUID] = mapped_column(
        ForeignKey("payroll_run_workers.id", ondelete="CASCADE")
    )
    deduction_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    pretax: Mapped[bool] = mapped_column(default=False)


class PayrollTaxLine(Base):
    __tablename__ = "payroll_tax_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_worker_id: Mapped[UUID] = mapped_column(
        ForeignKey("payroll_run_workers.id", ondelete="CASCADE")
    )
    tax_code: Mapped[str] = mapped_column(String(50))
    taxable_wages: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    employee_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    employer_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)


class PayrollLiability(Base):
    __tablename__ = "payroll_liabilities"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_run_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_runs.id", ondelete="CASCADE"))
    liability_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    open_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    status: Mapped[str] = mapped_column(String(30), default="open")


class PayrollPayment(Base):
    __tablename__ = "payroll_payments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_run_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_runs.id", ondelete="CASCADE"))
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    journal_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))


class PayrollReconciliationRun(Base):
    __tablename__ = "payroll_reconciliation_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_run_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_runs.id", ondelete="CASCADE"))
    subledger_total: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    gl_total: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    status: Mapped[str] = mapped_column(String(30))

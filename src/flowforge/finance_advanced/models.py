from __future__ import annotations

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


class TenantModel:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )


class CloseRun(TenantModel, Base):
    __tablename__ = "finance_close_runs"
    ledger_id: Mapped[UUID] = mapped_column(ForeignKey("ledgers.id"))
    period_id: Mapped[UUID] = mapped_column(ForeignKey("accounting_periods.id"))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    tolerance: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    blockers_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("tenant_id", "ledger_id", "period_id", name="uq_close_run_period"),
    )


class RecurringJournal(TenantModel, Base):
    __tablename__ = "finance_recurring_journals"
    code: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(String(300))
    ledger_id: Mapped[UUID] = mapped_column(ForeignKey("ledgers.id"))
    frequency: Mapped[str] = mapped_column(String(30))
    next_run_date: Mapped[date] = mapped_column(Date)
    debit_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    credit_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_recurring_journal_code"),)


class PaymentBatch(TenantModel, Base):
    __tablename__ = "finance_payment_batches"
    batch_number: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    currency_code: Mapped[str] = mapped_column(String(3))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_reference: Mapped[str | None] = mapped_column(String(200))
    __table_args__ = (
        UniqueConstraint("tenant_id", "batch_number", name="uq_payment_batch_number"),
    )


class ReconciliationSession(TenantModel, Base):
    __tablename__ = "finance_reconciliation_sessions"
    account_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id"))
    source_name: Mapped[str] = mapped_column(String(80))
    target_name: Mapped[str] = mapped_column(String(80))
    source_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    target_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    tolerance: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    status: Mapped[str] = mapped_column(String(30), default="open")
    variance: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    certified_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    evidence: Mapped[str] = mapped_column(Text, default="")


class BudgetVersion(TenantModel, Base):
    __tablename__ = "finance_budget_versions"
    code: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(200))
    fiscal_year: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_budget_version_code"),)


class BudgetLine(TenantModel, Base):
    __tablename__ = "finance_budget_lines"
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_budget_versions.id", ondelete="CASCADE")
    )
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    period_number: Mapped[int] = mapped_column(Integer)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    dimension_json: Mapped[str] = mapped_column(Text, default="{}")
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "version_id", "account_id", "period_number", name="uq_budget_line"
        ),
    )


class ConsolidationRun(TenantModel, Base):
    __tablename__ = "finance_consolidation_runs"
    code: Mapped[str] = mapped_column(String(80))
    as_of_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    source_entities: Mapped[int] = mapped_column(Integer, default=0)
    elimination_variance: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_consolidation_run_code"),)


class AssetRegister(TenantModel, Base):
    __tablename__ = "finance_asset_register"
    asset_number: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(240))
    acquisition_date: Mapped[date] = mapped_column(Date)
    cost: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    salvage_value: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    useful_life_periods: Mapped[int] = mapped_column(Integer)
    accumulated_depreciation: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    status: Mapped[str] = mapped_column(String(30), default="active")
    __table_args__ = (UniqueConstraint("tenant_id", "asset_number", name="uq_asset_number"),)

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


class Currency(Base):
    __tablename__ = "currencies"
    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "from_currency", "to_currency", "rate_date", name="uq_exchange_rate"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    from_currency: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    to_currency: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    rate_date: Mapped[date] = mapped_column(Date)
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 10))
    source: Mapped[str] = mapped_column(String(100), default="manual")


class FiscalCalendar(Base):
    __tablename__ = "fiscal_calendars"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    start_month: Mapped[int] = mapped_column(Integer, default=1)


class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "calendar_id", "period_code", name="uq_accounting_period"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    calendar_id: Mapped[UUID] = mapped_column(ForeignKey("fiscal_calendars.id", ondelete="CASCADE"))
    period_code: Mapped[str] = mapped_column(String(20))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="open")


class Ledger(Base):
    __tablename__ = "ledgers"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(150))
    base_currency: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "ledger_id", "account_code", name="uq_account_code"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ledger_id: Mapped[UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"), index=True
    )
    account_code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    account_type: Mapped[str] = mapped_column(String(30))
    normal_balance: Mapped[str] = mapped_column(String(10))
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id"))
    posting_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class FinancialDimension(Base):
    __tablename__ = "financial_dimensions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(150))
    required: Mapped[bool] = mapped_column(Boolean, default=False)


class DimensionValue(Base):
    __tablename__ = "dimension_values"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    dimension_id: Mapped[UUID] = mapped_column(
        ForeignKey("financial_dimensions.id", ondelete="CASCADE")
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ledger_id: Mapped[UUID] = mapped_column(ForeignKey("ledgers.id"), index=True)
    period_id: Mapped[UUID] = mapped_column(ForeignKey("accounting_periods.id"))
    journal_number: Mapped[str] = mapped_column(String(50))
    journal_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reversing_entry_id: Mapped[UUID | None] = mapped_column(ForeignKey("journal_entries.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JournalLine(Base):
    __tablename__ = "journal_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    journal_id: Mapped[UUID] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="CASCADE"), index=True
    )
    line_number: Mapped[int] = mapped_column(Integer)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    description: Mapped[str | None] = mapped_column(String(500))
    debit: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))


class AccountBalance(Base):
    __tablename__ = "account_balances"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "ledger_id", "period_id", "account_id", name="uq_account_balance"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ledger_id: Mapped[UUID] = mapped_column(ForeignKey("ledgers.id"))
    period_id: Mapped[UUID] = mapped_column(ForeignKey("accounting_periods.id"))
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    debit_total: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    credit_total: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)

"""Billing and preference tables (migration ff_billing_001)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class _Tenant:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingAccount(_Tenant, Base):
    """The workspace's card on file: Stripe ids and display details only, never card numbers."""

    __tablename__ = "billing_accounts"
    stripe_customer_id: Mapped[str | None] = mapped_column(String(80))
    payment_method_id: Mapped[str | None] = mapped_column(String(80))
    card_brand: Mapped[str | None] = mapped_column(String(30))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    card_exp_month: Mapped[int | None] = mapped_column(Integer)
    card_exp_year: Mapped[int | None] = mapped_column(Integer)
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    authorized_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    pending_checkout_session: Mapped[str | None] = mapped_column(String(120))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UsageDay(_Tenant, Base):
    __tablename__ = "usage_days"
    day: Mapped[date] = mapped_column(Date)
    storage_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    requests: Mapped[int] = mapped_column(Integer, default=0)
    bank_accounts: Mapped[int] = mapped_column(Integer, default=0)
    measured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BillingInvoice(_Tenant, Base):
    __tablename__ = "billing_invoices"
    number: Mapped[str] = mapped_column(String(40))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), default="usd")
    lines: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # open (waiting for its charge date) | paid | failed (retrying) | uncollected | void
    status: Mapped[str] = mapped_column(String(20), default="open")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    charge_on: Mapped[date] = mapped_column(Date)
    emailed_to: Mapped[str | None] = mapped_column(String(1000))
    emailed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_error: Mapped[str | None] = mapped_column(String(500))
    charge_attempts: Mapped[int] = mapped_column(Integer, default=0)
    charged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_intent_id: Mapped[str | None] = mapped_column(String(80))
    last_error: Mapped[str | None] = mapped_column(String(500))


class UserPreferences(_Tenant, Base):
    """What a person chose to hide (sidebar sections, home cards)."""

    __tablename__ = "user_preferences"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

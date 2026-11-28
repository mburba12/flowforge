"""Tables of the connections release: uploads, carrier accounts, tracked shipments and
payroll migration (migration ff_connect_001). Bank connections reuse bank_connections,
connected_bank_accounts and bank_transactions."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, deferred, mapped_column

from flowforge.db.base import Base


class _Tenant:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Attachment(_Tenant, Base):
    """A file a user uploaded in a section (an invoice, a receipt, a contract...)."""

    __tablename__ = "attachments"
    section: Mapped[str] = mapped_column(String(60), index=True)
    record_type: Mapped[str | None] = mapped_column(String(60))
    record_id: Mapped[str | None] = mapped_column(String(100))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(150))
    size_bytes: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[bytes] = deferred(mapped_column(LargeBinary))
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class CarrierAccount(_Tenant, Base):
    """A shipping carrier account (FedEx, UPS, USPS, DHL) with encrypted API credentials."""

    __tablename__ = "carrier_accounts"
    carrier: Mapped[str] = mapped_column(String(20))
    label: Mapped[str] = mapped_column(String(120))
    account_number_mask: Mapped[str | None] = mapped_column(String(20))
    encrypted_credentials: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="connected")
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(500))
    connected_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class TrackedShipment(_Tenant, Base):
    """A package followed through its carrier's tracking API."""

    __tablename__ = "tracked_shipments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "carrier", "tracking_number", name="uq_tracked_shipment"),
    )
    carrier: Mapped[str] = mapped_column(String(20))
    tracking_number: Mapped[str] = mapped_column(String(60))
    carrier_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("carrier_accounts.id", ondelete="SET NULL")
    )
    reference: Mapped[str | None] = mapped_column(String(200))
    direction: Mapped[str] = mapped_column(String(10), default="outbound")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    status_detail: Mapped[str | None] = mapped_column(String(300))
    estimated_delivery: Mapped[date | None] = mapped_column(Date)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_location: Mapped[str | None] = mapped_column(String(200))
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(500))
    added_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class PayrollMigration(_Tenant, Base):
    """One import of workers and pay history from a previous payroll provider."""

    __tablename__ = "payroll_migrations"
    provider: Mapped[str] = mapped_column(String(40))
    method: Mapped[str] = mapped_column(String(10))  # file | api
    status: Mapped[str] = mapped_column(String(20), default="pending")
    company_name: Mapped[str | None] = mapped_column(String(200))
    encrypted_tokens: Mapped[str | None] = mapped_column(Text)
    oauth_state: Mapped[str | None] = mapped_column(String(80))
    filename: Mapped[str | None] = mapped_column(String(255))
    tax_year: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list)
    started_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PayrollExternalWorker(_Tenant, Base):
    """Links a worker to their id at the previous provider, so re-imports update them."""

    __tablename__ = "payroll_external_workers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "external_id", name="uq_payroll_external_worker"),
    )
    provider: Mapped[str] = mapped_column(String(40))
    external_id: Mapped[str] = mapped_column(String(120))
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    email: Mapped[str | None] = mapped_column(String(320))


class PayrollYtdBalance(_Tenant, Base):
    """Year-to-date totals carried over from the previous provider (for W-2 continuity)."""

    __tablename__ = "payroll_ytd_balances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "worker_id", "tax_year", name="uq_payroll_ytd_balance"),
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    tax_year: Mapped[int] = mapped_column(Integer)
    gross_pay: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    federal_income_tax: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    social_security_tax: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    medicare_tax: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    state_income_tax: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    other_deductions: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    net_pay: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    migration_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payroll_migrations.id", ondelete="SET NULL")
    )

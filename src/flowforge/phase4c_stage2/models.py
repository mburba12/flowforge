from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class PaymentConnection(Base):
    __tablename__ = "payment_connections"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(40))
    provider_account_id: Mapped[str] = mapped_column(String(180))
    provider_merchant_id: Mapped[str | None] = mapped_column(String(180))
    credential_state: Mapped[str] = mapped_column(
        String(80), default="SANDBOX_CREDENTIAL_NOT_PERSISTED"
    )
    environment: Mapped[str] = mapped_column(String(20), default="sandbox")
    status: Mapped[str] = mapped_column(String(30), default="connected")
    connected_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MerchantLocation(Base):
    __tablename__ = "merchant_locations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "payment_connection_id",
            "provider_location_id",
            name="uq_merchant_location",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payment_connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment_connections.id", ondelete="CASCADE")
    )
    provider_location_id: Mapped[str] = mapped_column(String(180))
    name: Mapped[str] = mapped_column(String(200))
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PaymentTerminal(Base):
    __tablename__ = "payment_terminals"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "payment_connection_id", "provider_terminal_id", name="uq_payment_terminal"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payment_connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment_connections.id", ondelete="CASCADE")
    )
    merchant_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchant_locations.id", ondelete="SET NULL")
    )
    provider_terminal_id: Mapped[str] = mapped_column(String(180))
    label: Mapped[str] = mapped_column(String(200))
    serial_mask: Mapped[str | None] = mapped_column(String(12))
    status: Mapped[str] = mapped_column(String(30), default="unknown")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProcessorPayment(Base):
    __tablename__ = "processor_payments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "provider", "provider_payment_id", name="uq_processor_payment"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payment_connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment_connections.id", ondelete="CASCADE")
    )
    merchant_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchant_locations.id", ondelete="SET NULL")
    )
    terminal_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payment_terminals.id", ondelete="SET NULL")
    )
    provider: Mapped[str] = mapped_column(String(40))
    provider_payment_id: Mapped[str] = mapped_column(String(180))
    provider_order_id: Mapped[str | None] = mapped_column(String(180))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(30))
    payment_method_type: Mapped[str] = mapped_column(String(40))
    card_brand: Mapped[str | None] = mapped_column(String(30))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    livemode: Mapped[bool] = mapped_column(Boolean, default=False)


class ProcessorFee(Base):
    __tablename__ = "processor_fees"
    __table_args__ = (UniqueConstraint("tenant_id", "provider_fee_id", name="uq_processor_fee"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    processor_payment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("processor_payments.id", ondelete="CASCADE")
    )
    provider_fee_id: Mapped[str] = mapped_column(String(180))
    fee_type: Mapped[str] = mapped_column(String(40))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProcessorRefund(Base):
    __tablename__ = "processor_refunds"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider_refund_id", name="uq_processor_refund"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    processor_payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("processor_payments.id", ondelete="CASCADE")
    )
    provider_refund_id: Mapped[str] = mapped_column(String(180))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProcessorPayout(Base):
    __tablename__ = "processor_payouts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "provider_payout_id", name="uq_processor_payout"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payment_connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment_connections.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(40))
    provider_payout_id: Mapped[str] = mapped_column(String(180))
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    net_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    arrival_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30))


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_payment_webhook_event"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payment_connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payment_connections.id", ondelete="SET NULL")
    )
    provider: Mapped[str] = mapped_column(String(40))
    provider_event_id: Mapped[str] = mapped_column(String(180))
    event_type: Mapped[str] = mapped_column(String(100))
    signature_valid: Mapped[bool] = mapped_column(Boolean)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

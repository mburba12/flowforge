from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class BankConnection(Base):
    __tablename__ = "bank_connections"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(40))
    provider_item_id: Mapped[str | None] = mapped_column(String(150))
    institution_id: Mapped[str | None] = mapped_column(String(150))
    institution_name: Mapped[str | None] = mapped_column(String(200))
    encrypted_access_token: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    cursor: Mapped[str | None] = mapped_column(String(500))
    connected_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConnectedBankAccount(Base):
    __tablename__ = "connected_bank_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "provider_account_id", name="uq_connected_bank_account"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("bank_connections.id", ondelete="CASCADE")
    )
    provider_account_id: Mapped[str] = mapped_column(String(150))
    name: Mapped[str] = mapped_column(String(200))
    official_name: Mapped[str | None] = mapped_column(String(200))
    account_mask: Mapped[str | None] = mapped_column(String(8))
    account_type: Mapped[str] = mapped_column(String(40))
    account_subtype: Mapped[str | None] = mapped_column(String(50))
    currency_code: Mapped[str] = mapped_column(String(3))
    current_balance: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    import_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class BankAccountGLMapping(Base):
    __tablename__ = "bank_account_gl_mappings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connected_bank_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("connected_bank_accounts.id", ondelete="CASCADE"), unique=True
    )
    gl_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    mapping_type: Mapped[str] = mapped_column(String(40))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "provider", "provider_transaction_id", name="uq_bank_transaction_provider"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connected_bank_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("connected_bank_accounts.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(40))
    provider_transaction_id: Mapped[str] = mapped_column(String(180))
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    direction: Mapped[str] = mapped_column(String(10))
    original_description: Mapped[str] = mapped_column(String(500))
    normalized_description: Mapped[str | None] = mapped_column(String(500))
    pending: Mapped[bool] = mapped_column(Boolean, default=False)
    removed: Mapped[bool] = mapped_column(Boolean, default=False)


class BankBalanceSnapshot(Base):
    __tablename__ = "bank_balance_snapshots"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connected_bank_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("connected_bank_accounts.id", ondelete="CASCADE")
    )
    current_balance: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class BankSyncRun(Base):
    __tablename__ = "bank_sync_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("bank_connections.id", ondelete="CASCADE")
    )
    sync_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="running")
    transactions_created: Mapped[int] = mapped_column(default=0)
    transactions_updated: Mapped[int] = mapped_column(default=0)
    transactions_removed: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BankWebhookEvent(Base):
    __tablename__ = "bank_webhook_events"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_event_id",
            name="uq_bank_webhook_event",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(40))
    provider_event_id: Mapped[str] = mapped_column(String(180))
    connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "bank_connections.id",
            ondelete="SET NULL",
        )
    )
    event_type: Mapped[str] = mapped_column(String(100))
    signature_valid: Mapped[bool] = mapped_column(Boolean)
    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

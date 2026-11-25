from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
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


class FinanceConnection(Base):
    __tablename__ = "finance_connections"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "provider", "external_organization_id", name="uq_finance_connection"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(100))
    provider_family: Mapped[str] = mapped_column(String(60))
    external_organization_id: Mapped[str] = mapped_column(String(180))
    organization_name: Mapped[str] = mapped_column(String(240))
    credential_state: Mapped[str] = mapped_column(
        String(100), default="SANDBOX_CREDENTIAL_NOT_PERSISTED"
    )
    environment: Mapped[str] = mapped_column(String(20), default="sandbox")
    status: Mapped[str] = mapped_column(String(30), default="connected")
    cursor: Mapped[str | None] = mapped_column(String(500))
    connected_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExternalAccount(Base):
    __tablename__ = "finance_external_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_account_id", name="uq_finance_external_account"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    external_account_id: Mapped[str] = mapped_column(String(180))
    account_code: Mapped[str | None] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(240))
    account_type: Mapped[str] = mapped_column(String(60))
    currency_code: Mapped[str] = mapped_column(String(3))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class AccountMapping(Base):
    __tablename__ = "finance_account_mappings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_account_id", name="uq_finance_account_mapping"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    external_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_external_accounts.id", ondelete="CASCADE")
    )
    flowforge_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    mapping_status: Mapped[str] = mapped_column(String(30))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FinanceParty(Base):
    __tablename__ = "finance_parties"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "party_type", "external_party_id", name="uq_finance_party"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    party_type: Mapped[str] = mapped_column(String(30))
    external_party_id: Mapped[str] = mapped_column(String(180))
    display_name: Mapped[str] = mapped_column(String(240))
    email_hash: Mapped[str | None] = mapped_column(String(64))
    tax_identifier_mask: Mapped[str | None] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class FinanceDocument(Base):
    __tablename__ = "finance_documents"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "document_type",
            "external_document_id",
            name="uq_finance_document",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    party_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_parties.id", ondelete="SET NULL")
    )
    document_type: Mapped[str] = mapped_column(String(40))
    external_document_id: Mapped[str] = mapped_column(String(180))
    document_number: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    document_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class FinancePaymentStatus(Base):
    __tablename__ = "finance_payment_statuses"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_payment_id", name="uq_finance_payment_status"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_documents.id", ondelete="SET NULL")
    )
    external_payment_id: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(40))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    payment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    method_mask: Mapped[str | None] = mapped_column(String(40))


class ExternalJournalEntry(Base):
    __tablename__ = "finance_external_journal_entries"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_journal_id", name="uq_finance_external_journal"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    external_journal_id: Mapped[str] = mapped_column(String(180))
    entry_number: Mapped[str | None] = mapped_column(String(120))
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    memo: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40))
    currency_code: Mapped[str] = mapped_column(String(3))
    total_debits: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    total_credits: Mapped[Decimal] = mapped_column(Numeric(20, 2))


class ExternalJournalLine(Base):
    __tablename__ = "finance_external_journal_lines"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "journal_entry_id",
            "external_line_id",
            name="uq_finance_external_journal_line",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    journal_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_external_journal_entries.id", ondelete="CASCADE")
    )
    external_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_external_accounts.id", ondelete="SET NULL")
    )
    external_line_id: Mapped[str] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(String(300))
    debit: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    credit: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    dimensions: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class ExpenseTransaction(Base):
    __tablename__ = "finance_expense_transactions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_expense_id", name="uq_finance_expense"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    external_expense_id: Mapped[str] = mapped_column(String(180))
    merchant_name: Mapped[str | None] = mapped_column(String(240))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40))
    receipt_reference: Mapped[str | None] = mapped_column(String(500))


class TreasuryPosition(Base):
    __tablename__ = "finance_treasury_positions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_account_id",
            "as_of",
            name="uq_finance_treasury_position",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    external_account_id: Mapped[str] = mapped_column(String(180))
    account_mask: Mapped[str | None] = mapped_column(String(20))
    available_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReconciliationException(Base):
    __tablename__ = "finance_reconciliation_exceptions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    external_entity_id: Mapped[str] = mapped_column(String(180))
    exception_code: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30))
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FinanceSyncRun(Base):
    __tablename__ = "finance_sync_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="CASCADE")
    )
    sync_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))
    accounts_created: Mapped[int] = mapped_column(Integer, default=0)
    documents_created: Mapped[int] = mapped_column(Integer, default=0)
    expenses_created: Mapped[int] = mapped_column(Integer, default=0)
    exceptions_created: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FinanceWebhookEvent(Base):
    __tablename__ = "finance_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_finance_webhook_event"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_connections.id", ondelete="SET NULL")
    )
    provider: Mapped[str] = mapped_column(String(100))
    provider_event_id: Mapped[str] = mapped_column(String(180))
    event_type: Mapped[str] = mapped_column(String(100))
    signature_valid: Mapped[bool] = mapped_column(Boolean)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    payload_digest: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

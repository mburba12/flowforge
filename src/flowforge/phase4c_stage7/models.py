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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class EngagementConnection(Base):
    __tablename__ = "engagement_connections"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider",
            "external_organization_id",
            name="uq_engagement_connection",
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


class EngagementContact(Base):
    __tablename__ = "engagement_contacts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_contact_id",
            name="uq_engagement_contact",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    external_contact_id: Mapped[str] = mapped_column(String(180))
    display_name: Mapped[str] = mapped_column(String(240))
    email_hash: Mapped[str | None] = mapped_column(String(64))
    phone_mask: Mapped[str | None] = mapped_column(String(30))
    lifecycle_stage: Mapped[str | None] = mapped_column(String(60))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class EngagementAccount(Base):
    __tablename__ = "engagement_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_account_id",
            name="uq_engagement_account",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    external_account_id: Mapped[str] = mapped_column(String(180))
    name: Mapped[str] = mapped_column(String(240))
    industry: Mapped[str | None] = mapped_column(String(120))
    website_domain: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class EngagementLead(Base):
    __tablename__ = "engagement_leads"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_lead_id", name="uq_engagement_lead"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("engagement_contacts.id", ondelete="SET NULL")
    )
    external_lead_id: Mapped[str] = mapped_column(String(180))
    source: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    score: Mapped[int | None] = mapped_column(Integer)


class EngagementOpportunity(Base):
    __tablename__ = "engagement_opportunities"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_opportunity_id",
            name="uq_engagement_opportunity",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("engagement_accounts.id", ondelete="SET NULL")
    )
    external_opportunity_id: Mapped[str] = mapped_column(String(180))
    name: Mapped[str] = mapped_column(String(240))
    stage: Mapped[str] = mapped_column(String(80))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupportTicket(Base):
    __tablename__ = "engagement_support_tickets"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_ticket_id",
            name="uq_engagement_ticket",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("engagement_contacts.id", ondelete="SET NULL")
    )
    external_ticket_id: Mapped[str] = mapped_column(String(180))
    subject: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str | None] = mapped_column(String(30))
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupportMessage(Base):
    __tablename__ = "engagement_support_messages"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "ticket_id",
            "external_message_id",
            name="uq_engagement_support_message",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ticket_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_support_tickets.id", ondelete="CASCADE")
    )
    external_message_id: Mapped[str] = mapped_column(String(180))
    direction: Mapped[str] = mapped_column(String(20))
    sender_hash: Mapped[str | None] = mapped_column(String(64))
    body_digest: Mapped[str] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MarketingCampaign(Base):
    __tablename__ = "engagement_marketing_campaigns"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_campaign_id",
            name="uq_engagement_campaign",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    external_campaign_id: Mapped[str] = mapped_column(String(180))
    name: Mapped[str] = mapped_column(String(240))
    channel: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40))
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)


class EngagementActivity(Base):
    __tablename__ = "engagement_activities"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_activity_id",
            name="uq_engagement_activity",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("engagement_contacts.id", ondelete="SET NULL")
    )
    external_activity_id: Mapped[str] = mapped_column(String(180))
    activity_type: Mapped[str] = mapped_column(String(60))
    subject: Mapped[str | None] = mapped_column(String(300))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class CommunicationEvent(Base):
    __tablename__ = "engagement_communication_events"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_event_id",
            name="uq_engagement_communication_event",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    external_event_id: Mapped[str] = mapped_column(String(180))
    channel: Mapped[str] = mapped_column(String(40))
    direction: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(40))
    participant_mask: Mapped[str | None] = mapped_column(String(60))
    content_digest: Mapped[str | None] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EngagementSyncRun(Base):
    __tablename__ = "engagement_sync_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="CASCADE")
    )
    sync_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))
    contacts_created: Mapped[int] = mapped_column(Integer, default=0)
    opportunities_created: Mapped[int] = mapped_column(Integer, default=0)
    tickets_created: Mapped[int] = mapped_column(Integer, default=0)
    campaigns_created: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EngagementWebhookEvent(Base):
    __tablename__ = "engagement_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_engagement_webhook_event"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("engagement_connections.id", ondelete="SET NULL")
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

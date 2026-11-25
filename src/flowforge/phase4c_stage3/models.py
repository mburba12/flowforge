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


class CommerceConnection(Base):
    __tablename__ = "commerce_connections"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "provider", "external_store_id", name="uq_commerce_connection"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(80))
    provider_family: Mapped[str] = mapped_column(String(50))
    external_store_id: Mapped[str] = mapped_column(String(180))
    store_name: Mapped[str] = mapped_column(String(240))
    store_domain: Mapped[str | None] = mapped_column(String(300))
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


class CommerceCustomer(Base):
    __tablename__ = "commerce_customers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_customer_id", name="uq_commerce_customer"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    external_customer_id: Mapped[str] = mapped_column(String(180))
    email_hash: Mapped[str | None] = mapped_column(String(64))
    display_name: Mapped[str | None] = mapped_column(String(200))
    country_code: Mapped[str | None] = mapped_column(String(2))


class CommerceProduct(Base):
    __tablename__ = "commerce_products"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_product_id", name="uq_commerce_product"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    external_product_id: Mapped[str] = mapped_column(String(180))
    title: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(30))
    product_type: Mapped[str | None] = mapped_column(String(120))
    vendor: Mapped[str | None] = mapped_column(String(180))


class CommerceVariant(Base):
    __tablename__ = "commerce_variants"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_variant_id", name="uq_commerce_variant"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    commerce_product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("commerce_products.id", ondelete="CASCADE")
    )
    external_variant_id: Mapped[str] = mapped_column(String(180))
    sku: Mapped[str | None] = mapped_column(String(150))
    title: Mapped[str] = mapped_column(String(240))
    price: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    inventory_quantity: Mapped[int] = mapped_column(Integer, default=0)


class CommerceOrder(Base):
    __tablename__ = "commerce_orders"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_order_id", name="uq_commerce_order"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    commerce_customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("commerce_customers.id", ondelete="SET NULL")
    )
    external_order_id: Mapped[str] = mapped_column(String(180))
    order_number: Mapped[str] = mapped_column(String(120))
    order_status: Mapped[str] = mapped_column(String(40))
    financial_status: Mapped[str] = mapped_column(String(40))
    fulfillment_status: Mapped[str] = mapped_column(String(40))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    shipping_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    fee_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class CommerceOrderLine(Base):
    __tablename__ = "commerce_order_lines"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_line_id", name="uq_commerce_order_line"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    commerce_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_orders.id", ondelete="CASCADE")
    )
    commerce_variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("commerce_variants.id", ondelete="SET NULL")
    )
    external_line_id: Mapped[str] = mapped_column(String(180))
    sku: Mapped[str | None] = mapped_column(String(150))
    title: Mapped[str] = mapped_column(String(300))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    line_discount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    line_tax: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(20, 2))


class CommerceFulfillment(Base):
    __tablename__ = "commerce_fulfillments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_fulfillment_id", name="uq_commerce_fulfillment"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    commerce_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_orders.id", ondelete="CASCADE")
    )
    external_fulfillment_id: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(40))
    carrier: Mapped[str | None] = mapped_column(String(100))
    tracking_number_mask: Mapped[str | None] = mapped_column(String(50))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CommerceRefund(Base):
    __tablename__ = "commerce_refunds"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_refund_id", name="uq_commerce_refund"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    commerce_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_orders.id", ondelete="CASCADE")
    )
    external_refund_id: Mapped[str] = mapped_column(String(180))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(40))
    refunded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CommerceSettlement(Base):
    __tablename__ = "commerce_settlements"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_settlement_id", name="uq_commerce_settlement"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    external_settlement_id: Mapped[str] = mapped_column(String(180))
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    net_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    settlement_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40))


class CommerceSyncRun(Base):
    __tablename__ = "commerce_sync_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="CASCADE")
    )
    sync_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="running")
    products_created: Mapped[int] = mapped_column(Integer, default=0)
    orders_created: Mapped[int] = mapped_column(Integer, default=0)
    orders_updated: Mapped[int] = mapped_column(Integer, default=0)
    refunds_created: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CommerceWebhookEvent(Base):
    __tablename__ = "commerce_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_commerce_webhook_event"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("commerce_connections.id", ondelete="SET NULL")
    )
    provider: Mapped[str] = mapped_column(String(80))
    provider_event_id: Mapped[str] = mapped_column(String(180))
    event_type: Mapped[str] = mapped_column(String(100))
    signature_valid: Mapped[bool] = mapped_column(Boolean)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    payload_digest: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

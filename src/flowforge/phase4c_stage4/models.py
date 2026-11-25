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


class LogisticsConnection(Base):
    __tablename__ = "logistics_connections"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "provider", "external_account_id", name="uq_logistics_connection"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(80))
    provider_family: Mapped[str] = mapped_column(String(50))
    external_account_id: Mapped[str] = mapped_column(String(180))
    account_name: Mapped[str] = mapped_column(String(240))
    credential_state: Mapped[str] = mapped_column(
        String(100), default="SANDBOX_CREDENTIAL_NOT_PERSISTED"
    )
    environment: Mapped[str] = mapped_column(String(20), default="sandbox")
    status: Mapped[str] = mapped_column(String(30), default="connected")
    connected_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ShippingService(Base):
    __tablename__ = "shipping_services"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_service_id", name="uq_shipping_service"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_connections.id", ondelete="CASCADE")
    )
    external_service_id: Mapped[str] = mapped_column(String(180))
    name: Mapped[str] = mapped_column(String(180))
    service_code: Mapped[str] = mapped_column(String(80))
    domestic: Mapped[bool] = mapped_column(Boolean, default=True)
    international: Mapped[bool] = mapped_column(Boolean, default=False)
    tracking_supported: Mapped[bool] = mapped_column(Boolean, default=True)


class ShippingRateQuote(Base):
    __tablename__ = "shipping_rate_quotes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_connections.id", ondelete="CASCADE")
    )
    external_rate_id: Mapped[str] = mapped_column(String(180))
    service_code: Mapped[str] = mapped_column(String(80))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    estimated_days: Mapped[int | None] = mapped_column(Integer)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Shipment(Base):
    __tablename__ = "logistics_shipments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_shipment_id", name="uq_logistics_shipment"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_connections.id", ondelete="CASCADE")
    )
    external_shipment_id: Mapped[str] = mapped_column(String(180))
    commerce_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("commerce_orders.id", ondelete="SET NULL")
    )
    service_code: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40))
    tracking_number_mask: Mapped[str | None] = mapped_column(String(50))
    origin_country: Mapped[str] = mapped_column(String(2))
    destination_country: Mapped[str] = mapped_column(String(2))
    weight_grams: Mapped[int] = mapped_column(Integer)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class ShippingPackage(Base):
    __tablename__ = "shipping_packages"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "shipment_id", "external_package_id", name="uq_shipping_package"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    shipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_shipments.id", ondelete="CASCADE")
    )
    external_package_id: Mapped[str] = mapped_column(String(180))
    weight_grams: Mapped[int] = mapped_column(Integer)
    length_mm: Mapped[int | None] = mapped_column(Integer)
    width_mm: Mapped[int | None] = mapped_column(Integer)
    height_mm: Mapped[int | None] = mapped_column(Integer)


class ShippingLabel(Base):
    __tablename__ = "shipping_labels"
    __table_args__ = (UniqueConstraint("tenant_id", "external_label_id", name="uq_shipping_label"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    shipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_shipments.id", ondelete="CASCADE")
    )
    external_label_id: Mapped[str] = mapped_column(String(180))
    format: Mapped[str] = mapped_column(String(20))
    storage_reference: Mapped[str] = mapped_column(String(500))
    label_hash: Mapped[str] = mapped_column(String(64))
    voided: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "external_event_id", name="uq_tracking_event"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    shipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_shipments.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(80))
    external_event_id: Mapped[str] = mapped_column(String(180))
    status_code: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(String(300))
    location_summary: Mapped[str | None] = mapped_column(String(200))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReturnShipment(Base):
    __tablename__ = "return_shipments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connection_id", "external_return_id", name="uq_return_shipment"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_connections.id", ondelete="CASCADE")
    )
    original_shipment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("logistics_shipments.id", ondelete="SET NULL")
    )
    external_return_id: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(40))
    reason_code: Mapped[str | None] = mapped_column(String(80))
    tracking_number_mask: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FulfillmentOrder(Base):
    __tablename__ = "fulfillment_orders"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_fulfillment_order_id",
            name="uq_fulfillment_order",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_connections.id", ondelete="CASCADE")
    )
    external_fulfillment_order_id: Mapped[str] = mapped_column(String(180))
    commerce_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("commerce_orders.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(40))
    priority: Mapped[str] = mapped_column(String(30))
    requested_ship_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LogisticsInventoryBalance(Base):
    __tablename__ = "logistics_inventory_balances"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_sku",
            "external_location_id",
            name="uq_logistics_inventory_balance",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_connections.id", ondelete="CASCADE")
    )
    external_sku: Mapped[str] = mapped_column(String(180))
    external_location_id: Mapped[str] = mapped_column(String(180))
    available_quantity: Mapped[int] = mapped_column(Integer)
    reserved_quantity: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomsDocument(Base):
    __tablename__ = "customs_documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_document_id", name="uq_customs_document"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    shipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_shipments.id", ondelete="CASCADE")
    )
    external_document_id: Mapped[str] = mapped_column(String(180))
    document_type: Mapped[str] = mapped_column(String(60))
    storage_reference: Mapped[str] = mapped_column(String(500))
    document_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LogisticsSyncRun(Base):
    __tablename__ = "logistics_sync_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("logistics_connections.id", ondelete="CASCADE")
    )
    sync_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))
    shipments_created: Mapped[int] = mapped_column(Integer, default=0)
    tracking_events_created: Mapped[int] = mapped_column(Integer, default=0)
    inventory_updated: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LogisticsWebhookEvent(Base):
    __tablename__ = "logistics_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_logistics_webhook_event"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("logistics_connections.id", ondelete="SET NULL")
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

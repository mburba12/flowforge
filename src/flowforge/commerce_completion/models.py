from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class T:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LandedCost(T, Base):
    __tablename__ = "commerce_landed_costs"
    receipt_id: Mapped[UUID] = mapped_column(ForeignKey("goods_receipts.id"))
    cost_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    allocation_method: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="draft")


class Manifest(T, Base):
    __tablename__ = "commerce_manifests"
    manifest_number: Mapped[str] = mapped_column(String(100))
    carrier_code: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    shipment_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("tenant_id", "manifest_number", name="uq_manifest_number"),)


class CommerceEvent(T, Base):
    __tablename__ = "commerce_events_outbox"
    event_type: Mapped[str] = mapped_column(String(100))
    aggregate_type: Mapped[str] = mapped_column(String(60))
    aggregate_id: Mapped[UUID]
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class T:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1)


class ManufacturingRecord(T, Base):
    __tablename__ = "bg09_manufacturing_records"
    record_type: Mapped[str] = mapped_column(String(60))
    code: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    parent_id: Mapped[UUID | None]
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "record_type", "code", "revision", name="uq_bg09_record"),
    )


class GenealogyEdge(T, Base):
    __tablename__ = "bg09_genealogy_edges"
    parent_lot: Mapped[str] = mapped_column(String(160))
    child_lot: Mapped[str] = mapped_column(String(160))
    work_order_code: Mapped[str] = mapped_column(String(100))
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "parent_lot", "child_lot", "work_order_code", name="uq_bg09_genealogy"
        ),
    )

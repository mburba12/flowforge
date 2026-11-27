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


class InformationRecord(T, Base):
    __tablename__ = "bg10_information_records"
    record_type: Mapped[str] = mapped_column(String(60))
    code: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="active")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    permission_code: Mapped[str | None] = mapped_column(String(120))
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("tenant_id", "record_type", "code", name="uq_bg10_record"),)


class CopilotProposal(T, Base):
    __tablename__ = "bg10_copilot_proposals"
    prompt_hash: Mapped[str] = mapped_column(String(128))
    context_json: Mapped[str] = mapped_column(Text)
    response_json: Mapped[str] = mapped_column(Text)
    citations_json: Mapped[str] = mapped_column(Text, default="[]")
    risk: Mapped[str] = mapped_column(String(20), default="low")
    status: Mapped[str] = mapped_column(String(30), default="proposed")
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    cost_micros: Mapped[int] = mapped_column(Integer, default=0)

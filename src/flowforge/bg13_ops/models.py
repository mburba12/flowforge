from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class T:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1)


class OperationalRun(T, Base):
    __tablename__ = "bg13_operational_runs"
    run_type: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30), default="requested")
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class SalesOrderStatusEvent(Base):
    """Append-only status history of a sales order (customer-visible order tracking)."""

    __tablename__ = "sales_order_status_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("sales_orders.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(String(300))
    changed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


async def record_order_status(
    db: object,
    tenant_id: UUID,
    order_id: UUID,
    status: str,
    user_id: UUID | None,
    note: str | None = None,
) -> None:
    db.add(  # type: ignore[attr-defined]
        SalesOrderStatusEvent(
            tenant_id=tenant_id, order_id=order_id, status=status, changed_by=user_id, note=note
        )
    )

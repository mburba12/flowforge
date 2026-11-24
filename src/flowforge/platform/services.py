from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.platform.models import AuditEntry, DomainEvent


async def record_change(
    db: AsyncSession,
    tenant_id: UUID,
    actor_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: str,
    payload: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditEntry(
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload or {},
        )
    )
    db.add(
        DomainEvent(
            tenant_id=tenant_id,
            event_type=f"{resource_type}.{action}",
            aggregate_type=resource_type,
            aggregate_id=resource_id,
            payload=payload or {},
        )
    )

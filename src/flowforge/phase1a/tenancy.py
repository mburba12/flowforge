from dataclasses import dataclass
from uuid import UUID

from .errors import TenantIsolationError


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: UUID
    user_id: UUID


def require_tenant(ctx: TenantContext, record_tenant_id: UUID) -> None:
    if ctx.tenant_id != record_tenant_id:
        raise TenantIsolationError("Cross-tenant access denied")


def tenant_filter(ctx: TenantContext) -> dict[str, UUID]:
    return {"tenant_id": ctx.tenant_id}

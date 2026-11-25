from contextvars import ContextVar, Token
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TenantSecurityContext:
    tenant_id: UUID
    user_id: UUID
    session_id: UUID | None = None


_current: ContextVar[TenantSecurityContext | None] = ContextVar(
    "tenant_security_context", default=None
)


def set_tenant_context(context: TenantSecurityContext) -> Token[TenantSecurityContext | None]:
    return _current.set(context)


def reset_tenant_context(token: Token[TenantSecurityContext | None]) -> None:
    _current.reset(token)


def require_tenant_context() -> TenantSecurityContext:
    context = _current.get()
    if context is None:
        raise RuntimeError("Verified tenant context is required")
    return context

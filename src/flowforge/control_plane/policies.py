from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from flowforge.core.errors import RuleViolation


@dataclass(frozen=True, slots=True)
class CommandContext:
    tenant_id: UUID
    actor_user_id: UUID
    idempotency_key: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ProviderWritePolicy:
    enabled: bool = False
    sandbox_only: bool = True
    approval_required: bool = True

    def assert_allowed(self, *, sandbox: bool, approved: bool) -> None:
        if not self.enabled:
            raise RuleViolation("Provider writes are disabled")
        if self.sandbox_only and not sandbox:
            raise RuleViolation("Production provider writes are disabled")
        if self.approval_required and not approved:
            raise RuleViolation("Provider write approval is required")


def new_context(tenant_id: UUID, actor_user_id: UUID, idempotency_key: str) -> CommandContext:
    if not idempotency_key.strip():
        raise ValueError("idempotency_key is required")
    return CommandContext(tenant_id, actor_user_id, idempotency_key, datetime.now(UTC))

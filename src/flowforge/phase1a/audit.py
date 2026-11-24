import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from uuid import UUID

from .clock import utcnow


@dataclass(frozen=True, slots=True)
class AuditEvent:
    tenant_id: UUID
    actor_id: UUID | None
    action: str
    resource_type: str
    resource_id: str
    at: datetime
    previous_hash: str
    event_hash: str


class AuditChain:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(
        self,
        tenant_id: UUID,
        actor_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: str,
    ) -> AuditEvent:
        prev = self.events[-1].event_hash if self.events else "0" * 64
        at = utcnow()
        body = json.dumps(
            [
                str(tenant_id),
                str(actor_id),
                action,
                resource_type,
                resource_id,
                at.isoformat(),
                prev,
            ]
        )
        h = sha256(body.encode()).hexdigest()
        e = AuditEvent(tenant_id, actor_id, action, resource_type, resource_id, at, prev, h)
        self.events.append(e)
        return e

    def verify(self) -> bool:
        return all(
            e.previous_hash == (self.events[i - 1].event_hash if i else "0" * 64)
            for i, e in enumerate(self.events)
        )

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from .clock import utcnow


@dataclass(slots=True)
class OutboxEvent:
    id: UUID
    tenant_id: UUID
    kind: str
    payload: dict[str, object]
    created_at: datetime
    attempts: int = 0
    published_at: datetime | None = None
    dead: bool = False


class Outbox:
    def __init__(self, max_attempts: int = 5) -> None:
        self.events: list[OutboxEvent] = []
        self.max_attempts = max_attempts

    def add(self, tenant_id: UUID, kind: str, payload: dict[str, object]) -> OutboxEvent:
        e = OutboxEvent(uuid4(), tenant_id, kind, payload, utcnow())
        self.events.append(e)
        return e

    def pending(self) -> list[OutboxEvent]:
        return [e for e in self.events if e.published_at is None and not e.dead]

    def success(self, e: OutboxEvent) -> None:
        e.published_at = utcnow()

    def failure(self, e: OutboxEvent) -> None:
        e.attempts += 1
        e.dead = e.attempts >= self.max_attempts

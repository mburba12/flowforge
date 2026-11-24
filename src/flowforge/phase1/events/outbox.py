"""FlowForge Phase 1 events.outbox component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OutboxComponent:
    """Typed boundary for the outbox capability."""

    name: str = "events.outbox"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 events.idempotency component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class IdempotencyComponent:
    """Typed boundary for the idempotency capability."""

    name: str = "events.idempotency"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

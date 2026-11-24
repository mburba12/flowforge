"""FlowForge Phase 1 events.dead_letters component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DeadLettersComponent:
    """Typed boundary for the dead letters capability."""

    name: str = "events.dead_letters"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

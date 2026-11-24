"""FlowForge Phase 1 operations.health component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class HealthComponent:
    """Typed boundary for the health capability."""

    name: str = "operations.health"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 authorization.separation_of_duties component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SeparationOfDutiesComponent:
    """Typed boundary for the separation of duties capability."""

    name: str = "authorization.separation_of_duties"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 events.routes component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RoutesComponent:
    """Typed boundary for the routes capability."""

    name: str = "events.routes"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

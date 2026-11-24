"""FlowForge Phase 1 events.monitoring component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MonitoringComponent:
    """Typed boundary for the monitoring capability."""

    name: str = "events.monitoring"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

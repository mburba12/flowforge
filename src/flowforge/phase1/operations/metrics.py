"""FlowForge Phase 1 operations.metrics component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MetricsComponent:
    """Typed boundary for the metrics capability."""

    name: str = "operations.metrics"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

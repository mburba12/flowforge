"""FlowForge Phase 1 operations.correlation component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CorrelationComponent:
    """Typed boundary for the correlation capability."""

    name: str = "operations.correlation"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

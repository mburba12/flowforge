"""FlowForge Phase 1 operations.tracing component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TracingComponent:
    """Typed boundary for the tracing capability."""

    name: str = "operations.tracing"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

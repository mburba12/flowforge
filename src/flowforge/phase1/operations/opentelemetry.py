"""FlowForge Phase 1 operations.opentelemetry component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OpentelemetryComponent:
    """Typed boundary for the opentelemetry capability."""

    name: str = "operations.opentelemetry"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

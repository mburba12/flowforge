"""FlowForge Phase 1 operations.liveness component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LivenessComponent:
    """Typed boundary for the liveness capability."""

    name: str = "operations.liveness"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

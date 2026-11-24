"""FlowForge Phase 1 operations.request_limits component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RequestLimitsComponent:
    """Typed boundary for the request limits capability."""

    name: str = "operations.request_limits"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

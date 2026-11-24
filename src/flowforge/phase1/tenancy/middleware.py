"""FlowForge Phase 1 tenancy.middleware component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MiddlewareComponent:
    """Typed boundary for the middleware capability."""

    name: str = "tenancy.middleware"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

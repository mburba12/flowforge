"""FlowForge Phase 1 authorization.service component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ServiceComponent:
    """Typed boundary for the service capability."""

    name: str = "authorization.service"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

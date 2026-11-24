"""FlowForge Phase 1 documents.service component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ServiceComponent:
    """Typed boundary for the service capability."""

    name: str = "documents.service"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

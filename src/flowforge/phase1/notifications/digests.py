"""FlowForge Phase 1 notifications.digests component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DigestsComponent:
    """Typed boundary for the digests capability."""

    name: str = "notifications.digests"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 notifications.dispatcher component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DispatcherComponent:
    """Typed boundary for the dispatcher capability."""

    name: str = "notifications.dispatcher"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

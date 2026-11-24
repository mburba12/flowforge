"""FlowForge Phase 1 notifications.in_app component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class InAppComponent:
    """Typed boundary for the in app capability."""

    name: str = "notifications.in_app"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

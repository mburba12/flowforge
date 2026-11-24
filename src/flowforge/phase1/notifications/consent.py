"""FlowForge Phase 1 notifications.consent component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ConsentComponent:
    """Typed boundary for the consent capability."""

    name: str = "notifications.consent"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

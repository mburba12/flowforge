"""FlowForge Phase 1 notifications.email component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EmailComponent:
    """Typed boundary for the email capability."""

    name: str = "notifications.email"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

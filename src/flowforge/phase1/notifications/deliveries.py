"""FlowForge Phase 1 notifications.deliveries component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DeliveriesComponent:
    """Typed boundary for the deliveries capability."""

    name: str = "notifications.deliveries"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

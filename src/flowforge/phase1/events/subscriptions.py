"""FlowForge Phase 1 events.subscriptions component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SubscriptionsComponent:
    """Typed boundary for the subscriptions capability."""

    name: str = "events.subscriptions"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

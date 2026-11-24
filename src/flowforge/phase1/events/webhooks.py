"""FlowForge Phase 1 events.webhooks component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class WebhooksComponent:
    """Typed boundary for the webhooks capability."""

    name: str = "events.webhooks"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

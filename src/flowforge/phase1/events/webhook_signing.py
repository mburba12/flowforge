"""FlowForge Phase 1 events.webhook_signing component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class WebhookSigningComponent:
    """Typed boundary for the webhook signing capability."""

    name: str = "events.webhook_signing"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

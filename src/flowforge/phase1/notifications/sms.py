"""FlowForge Phase 1 notifications.sms component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SmsComponent:
    """Typed boundary for the sms capability."""

    name: str = "notifications.sms"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

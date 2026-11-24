"""FlowForge Phase 1 notifications.localization component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LocalizationComponent:
    """Typed boundary for the localization capability."""

    name: str = "notifications.localization"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

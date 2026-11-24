"""FlowForge Phase 1 notifications.preferences component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PreferencesComponent:
    """Typed boundary for the preferences capability."""

    name: str = "notifications.preferences"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

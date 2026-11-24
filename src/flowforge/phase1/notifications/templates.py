"""FlowForge Phase 1 notifications.templates component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TemplatesComponent:
    """Typed boundary for the templates capability."""

    name: str = "notifications.templates"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 notifications.schemas component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SchemasComponent:
    """Typed boundary for the schemas capability."""

    name: str = "notifications.schemas"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 documents.permissions component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PermissionsComponent:
    """Typed boundary for the permissions capability."""

    name: str = "documents.permissions"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

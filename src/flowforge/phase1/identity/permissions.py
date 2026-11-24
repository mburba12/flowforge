"""FlowForge Phase 1 identity.permissions component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PermissionsComponent:
    """Typed boundary for the permissions capability."""

    name: str = "identity.permissions"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

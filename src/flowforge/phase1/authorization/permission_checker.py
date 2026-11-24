"""FlowForge Phase 1 authorization.permission_checker component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PermissionCheckerComponent:
    """Typed boundary for the permission checker capability."""

    name: str = "authorization.permission_checker"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

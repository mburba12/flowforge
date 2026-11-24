"""FlowForge Phase 1 authorization.system_roles component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SystemRolesComponent:
    """Typed boundary for the system roles capability."""

    name: str = "authorization.system_roles"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

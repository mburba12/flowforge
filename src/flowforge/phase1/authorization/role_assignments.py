"""FlowForge Phase 1 authorization.role_assignments component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RoleAssignmentsComponent:
    """Typed boundary for the role assignments capability."""

    name: str = "authorization.role_assignments"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 authorization.custom_roles component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CustomRolesComponent:
    """Typed boundary for the custom roles capability."""

    name: str = "authorization.custom_roles"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

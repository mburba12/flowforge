"""FlowForge Phase 1 tenancy.admin_boundaries component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AdminBoundariesComponent:
    """Typed boundary for the admin boundaries capability."""

    name: str = "tenancy.admin_boundaries"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 tenancy.row_level_security component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RowLevelSecurityComponent:
    """Typed boundary for the row level security capability."""

    name: str = "tenancy.row_level_security"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

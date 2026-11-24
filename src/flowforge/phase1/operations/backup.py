"""FlowForge Phase 1 operations.backup component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BackupComponent:
    """Typed boundary for the backup capability."""

    name: str = "operations.backup"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

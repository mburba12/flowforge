"""FlowForge Phase 1 operations.restore component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RestoreComponent:
    """Typed boundary for the restore capability."""

    name: str = "operations.restore"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

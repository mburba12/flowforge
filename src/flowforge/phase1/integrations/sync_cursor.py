"""FlowForge Phase 1 integrations.sync_cursor component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SyncCursorComponent:
    """Typed boundary for the sync cursor capability."""

    name: str = "integrations.sync_cursor"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

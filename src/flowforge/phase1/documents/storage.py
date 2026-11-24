"""FlowForge Phase 1 documents.storage component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class StorageComponent:
    """Typed boundary for the storage capability."""

    name: str = "documents.storage"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

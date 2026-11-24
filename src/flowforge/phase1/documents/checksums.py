"""FlowForge Phase 1 documents.checksums component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ChecksumsComponent:
    """Typed boundary for the checksums capability."""

    name: str = "documents.checksums"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

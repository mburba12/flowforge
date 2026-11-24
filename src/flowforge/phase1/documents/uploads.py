"""FlowForge Phase 1 documents.uploads component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class UploadsComponent:
    """Typed boundary for the uploads capability."""

    name: str = "documents.uploads"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

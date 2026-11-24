"""FlowForge Phase 1 documents.previews component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PreviewsComponent:
    """Typed boundary for the previews capability."""

    name: str = "documents.previews"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

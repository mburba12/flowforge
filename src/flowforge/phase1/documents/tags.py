"""FlowForge Phase 1 documents.tags component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TagsComponent:
    """Typed boundary for the tags capability."""

    name: str = "documents.tags"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

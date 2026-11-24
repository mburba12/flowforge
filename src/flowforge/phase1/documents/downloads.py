"""FlowForge Phase 1 documents.downloads component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DownloadsComponent:
    """Typed boundary for the downloads capability."""

    name: str = "documents.downloads"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 documents.versions component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class VersionsComponent:
    """Typed boundary for the versions capability."""

    name: str = "documents.versions"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

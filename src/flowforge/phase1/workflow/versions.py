"""FlowForge Phase 1 workflow.versions component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class VersionsComponent:
    """Typed boundary for the versions capability."""

    name: str = "workflow.versions"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

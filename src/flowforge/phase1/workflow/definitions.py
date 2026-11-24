"""FlowForge Phase 1 workflow.definitions component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DefinitionsComponent:
    """Typed boundary for the definitions capability."""

    name: str = "workflow.definitions"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

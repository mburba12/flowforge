"""FlowForge Phase 1 workflow.models component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ModelsComponent:
    """Typed boundary for the models capability."""

    name: str = "workflow.models"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

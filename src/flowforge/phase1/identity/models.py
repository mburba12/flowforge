"""FlowForge Phase 1 identity.models component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ModelsComponent:
    """Typed boundary for the models capability."""

    name: str = "identity.models"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

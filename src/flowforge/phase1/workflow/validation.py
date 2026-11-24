"""FlowForge Phase 1 workflow.validation component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ValidationComponent:
    """Typed boundary for the validation capability."""

    name: str = "workflow.validation"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

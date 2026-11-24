"""FlowForge Phase 1 workflow.steps component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class StepsComponent:
    """Typed boundary for the steps capability."""

    name: str = "workflow.steps"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

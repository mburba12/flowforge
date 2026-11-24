"""FlowForge Phase 1 workflow.assignments component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AssignmentsComponent:
    """Typed boundary for the assignments capability."""

    name: str = "workflow.assignments"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

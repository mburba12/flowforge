"""FlowForge Phase 1 workflow.tasks component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TasksComponent:
    """Typed boundary for the tasks capability."""

    name: str = "workflow.tasks"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 workflow.reminders component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RemindersComponent:
    """Typed boundary for the reminders capability."""

    name: str = "workflow.reminders"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

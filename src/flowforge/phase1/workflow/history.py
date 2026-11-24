"""FlowForge Phase 1 workflow.history component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class HistoryComponent:
    """Typed boundary for the history capability."""

    name: str = "workflow.history"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

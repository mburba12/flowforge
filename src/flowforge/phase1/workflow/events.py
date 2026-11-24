"""FlowForge Phase 1 workflow.events component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EventsComponent:
    """Typed boundary for the events capability."""

    name: str = "workflow.events"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

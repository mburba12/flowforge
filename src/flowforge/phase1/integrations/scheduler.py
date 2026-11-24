"""FlowForge Phase 1 integrations.scheduler component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SchedulerComponent:
    """Typed boundary for the scheduler capability."""

    name: str = "integrations.scheduler"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

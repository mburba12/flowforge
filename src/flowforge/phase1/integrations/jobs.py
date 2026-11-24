"""FlowForge Phase 1 integrations.jobs component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class JobsComponent:
    """Typed boundary for the jobs capability."""

    name: str = "integrations.jobs"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

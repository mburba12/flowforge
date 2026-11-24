"""FlowForge Phase 1 workflow.instances component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class InstancesComponent:
    """Typed boundary for the instances capability."""

    name: str = "workflow.instances"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 workflow.parallel component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ParallelComponent:
    """Typed boundary for the parallel capability."""

    name: str = "workflow.parallel"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

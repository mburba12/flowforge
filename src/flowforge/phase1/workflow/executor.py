"""FlowForge Phase 1 workflow.executor component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ExecutorComponent:
    """Typed boundary for the executor capability."""

    name: str = "workflow.executor"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

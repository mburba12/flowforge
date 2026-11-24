"""FlowForge Phase 1 workflow.escalations component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EscalationsComponent:
    """Typed boundary for the escalations capability."""

    name: str = "workflow.escalations"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

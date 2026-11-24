"""FlowForge Phase 1 workflow.delegations component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DelegationsComponent:
    """Typed boundary for the delegations capability."""

    name: str = "workflow.delegations"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

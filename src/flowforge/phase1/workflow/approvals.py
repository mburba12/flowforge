"""FlowForge Phase 1 workflow.approvals component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ApprovalsComponent:
    """Typed boundary for the approvals capability."""

    name: str = "workflow.approvals"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

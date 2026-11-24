"""FlowForge Phase 1 authorization.approval_limits component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ApprovalLimitsComponent:
    """Typed boundary for the approval limits capability."""

    name: str = "authorization.approval_limits"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

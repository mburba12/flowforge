"""FlowForge Phase 1 authorization.policies component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PoliciesComponent:
    """Typed boundary for the policies capability."""

    name: str = "authorization.policies"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

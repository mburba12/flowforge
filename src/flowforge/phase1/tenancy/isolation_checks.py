"""FlowForge Phase 1 tenancy.isolation_checks component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class IsolationChecksComponent:
    """Typed boundary for the isolation checks capability."""

    name: str = "tenancy.isolation_checks"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

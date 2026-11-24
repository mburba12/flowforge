"""FlowForge Phase 1 tenancy.job_scope component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class JobScopeComponent:
    """Typed boundary for the job scope capability."""

    name: str = "tenancy.job_scope"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

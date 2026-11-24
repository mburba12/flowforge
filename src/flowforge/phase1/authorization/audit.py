"""FlowForge Phase 1 authorization.audit component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AuditComponent:
    """Typed boundary for the audit capability."""

    name: str = "authorization.audit"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

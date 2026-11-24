"""FlowForge Phase 1 operations.security_headers component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SecurityHeadersComponent:
    """Typed boundary for the security headers capability."""

    name: str = "operations.security_headers"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

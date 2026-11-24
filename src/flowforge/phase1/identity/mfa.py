"""FlowForge Phase 1 identity.mfa component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MfaComponent:
    """Typed boundary for the mfa capability."""

    name: str = "identity.mfa"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

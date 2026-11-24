"""FlowForge Phase 1 identity.password_reset component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PasswordResetComponent:
    """Typed boundary for the password reset capability."""

    name: str = "identity.password_reset"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

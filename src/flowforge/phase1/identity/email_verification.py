"""FlowForge Phase 1 identity.email_verification component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EmailVerificationComponent:
    """Typed boundary for the email verification capability."""

    name: str = "identity.email_verification"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

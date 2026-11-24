"""FlowForge Phase 1 identity.invitations component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class InvitationsComponent:
    """Typed boundary for the invitations capability."""

    name: str = "identity.invitations"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

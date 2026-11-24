"""FlowForge Phase 1 identity.sessions component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SessionsComponent:
    """Typed boundary for the sessions capability."""

    name: str = "identity.sessions"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

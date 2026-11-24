"""FlowForge Phase 1 identity.refresh_tokens component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RefreshTokensComponent:
    """Typed boundary for the refresh tokens capability."""

    name: str = "identity.refresh_tokens"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

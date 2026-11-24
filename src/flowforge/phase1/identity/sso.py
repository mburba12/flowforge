"""FlowForge Phase 1 identity.sso component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SsoComponent:
    """Typed boundary for the sso capability."""

    name: str = "identity.sso"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

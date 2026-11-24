"""FlowForge Phase 1 identity.passwords component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PasswordsComponent:
    """Typed boundary for the passwords capability."""

    name: str = "identity.passwords"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 integrations.credentials component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CredentialsComponent:
    """Typed boundary for the credentials capability."""

    name: str = "integrations.credentials"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

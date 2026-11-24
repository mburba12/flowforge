"""FlowForge Phase 1 operations.key_vault component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class KeyVaultComponent:
    """Typed boundary for the key vault capability."""

    name: str = "operations.key_vault"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

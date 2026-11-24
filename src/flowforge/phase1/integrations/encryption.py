"""FlowForge Phase 1 integrations.encryption component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EncryptionComponent:
    """Typed boundary for the encryption capability."""

    name: str = "integrations.encryption"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 integrations.azure component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AzureComponent:
    """Typed boundary for the azure capability."""

    name: str = "integrations.azure"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

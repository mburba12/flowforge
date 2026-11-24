"""FlowForge Phase 1 documents.azure_blob component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AzureBlobComponent:
    """Typed boundary for the azure blob capability."""

    name: str = "documents.azure_blob"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

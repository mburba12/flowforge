"""FlowForge Phase 1 documents.schemas component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SchemasComponent:
    """Typed boundary for the schemas capability."""

    name: str = "documents.schemas"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

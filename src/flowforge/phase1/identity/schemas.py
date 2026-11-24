"""FlowForge Phase 1 identity.schemas component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SchemasComponent:
    """Typed boundary for the schemas capability."""

    name: str = "identity.schemas"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

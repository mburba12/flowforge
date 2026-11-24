"""FlowForge Phase 1 authorization.schemas component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SchemasComponent:
    """Typed boundary for the schemas capability."""

    name: str = "authorization.schemas"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

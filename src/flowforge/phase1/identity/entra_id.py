"""FlowForge Phase 1 identity.entra_id component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EntraIdComponent:
    """Typed boundary for the entra id capability."""

    name: str = "identity.entra_id"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

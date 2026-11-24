"""FlowForge Phase 1 operations.errors component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ErrorsComponent:
    """Typed boundary for the errors capability."""

    name: str = "operations.errors"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

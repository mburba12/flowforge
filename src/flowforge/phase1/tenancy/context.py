"""FlowForge Phase 1 tenancy.context component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ContextComponent:
    """Typed boundary for the context capability."""

    name: str = "tenancy.context"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

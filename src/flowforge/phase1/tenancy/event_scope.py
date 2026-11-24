"""FlowForge Phase 1 tenancy.event_scope component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EventScopeComponent:
    """Typed boundary for the event scope capability."""

    name: str = "tenancy.event_scope"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

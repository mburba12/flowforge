"""FlowForge Phase 1 events.replay component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ReplayComponent:
    """Typed boundary for the replay capability."""

    name: str = "events.replay"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

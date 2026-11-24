"""FlowForge Phase 1 events.publisher component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PublisherComponent:
    """Typed boundary for the publisher capability."""

    name: str = "events.publisher"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

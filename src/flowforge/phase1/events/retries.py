"""FlowForge Phase 1 events.retries component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RetriesComponent:
    """Typed boundary for the retries capability."""

    name: str = "events.retries"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

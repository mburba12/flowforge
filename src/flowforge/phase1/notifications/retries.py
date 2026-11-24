"""FlowForge Phase 1 notifications.retries component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RetriesComponent:
    """Typed boundary for the retries capability."""

    name: str = "notifications.retries"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

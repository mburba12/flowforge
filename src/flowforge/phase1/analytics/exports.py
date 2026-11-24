"""FlowForge Phase 1 analytics.exports component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ExportsComponent:
    """Typed boundary for the exports capability."""

    name: str = "analytics.exports"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 search.query component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class QueryComponent:
    """Typed boundary for the query capability."""

    name: str = "search.query"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

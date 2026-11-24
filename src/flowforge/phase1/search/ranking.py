"""FlowForge Phase 1 search.ranking component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RankingComponent:
    """Typed boundary for the ranking capability."""

    name: str = "search.ranking"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 search.indexer component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class IndexerComponent:
    """Typed boundary for the indexer capability."""

    name: str = "search.indexer"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

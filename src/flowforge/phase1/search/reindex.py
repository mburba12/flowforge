"""FlowForge Phase 1 search.reindex component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ReindexComponent:
    """Typed boundary for the reindex capability."""

    name: str = "search.reindex"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

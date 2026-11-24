"""FlowForge Phase 1 search.filters component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FiltersComponent:
    """Typed boundary for the filters capability."""

    name: str = "search.filters"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

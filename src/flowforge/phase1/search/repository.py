"""FlowForge Phase 1 search.repository component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RepositoryComponent:
    """Typed boundary for the repository capability."""

    name: str = "search.repository"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

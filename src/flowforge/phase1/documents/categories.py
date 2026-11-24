"""FlowForge Phase 1 documents.categories component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CategoriesComponent:
    """Typed boundary for the categories capability."""

    name: str = "documents.categories"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 documents.retention component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RetentionComponent:
    """Typed boundary for the retention capability."""

    name: str = "documents.retention"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

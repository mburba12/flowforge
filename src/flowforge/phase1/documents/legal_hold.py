"""FlowForge Phase 1 documents.legal_hold component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LegalHoldComponent:
    """Typed boundary for the legal hold capability."""

    name: str = "documents.legal_hold"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

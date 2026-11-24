"""FlowForge Phase 1 documents.ocr_handoff component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OcrHandoffComponent:
    """Typed boundary for the ocr handoff capability."""

    name: str = "documents.ocr_handoff"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

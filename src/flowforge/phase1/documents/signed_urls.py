"""FlowForge Phase 1 documents.signed_urls component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SignedUrlsComponent:
    """Typed boundary for the signed urls capability."""

    name: str = "documents.signed_urls"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

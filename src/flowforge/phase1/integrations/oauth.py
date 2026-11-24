"""FlowForge Phase 1 integrations.oauth component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OauthComponent:
    """Typed boundary for the oauth capability."""

    name: str = "integrations.oauth"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

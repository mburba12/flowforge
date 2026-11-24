"""FlowForge Phase 1 identity.api_keys component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ApiKeysComponent:
    """Typed boundary for the api keys capability."""

    name: str = "identity.api_keys"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

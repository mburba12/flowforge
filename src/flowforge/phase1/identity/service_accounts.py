"""FlowForge Phase 1 identity.service_accounts component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ServiceAccountsComponent:
    """Typed boundary for the service accounts capability."""

    name: str = "identity.service_accounts"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

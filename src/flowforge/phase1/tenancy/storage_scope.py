"""FlowForge Phase 1 tenancy.storage_scope component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class StorageScopeComponent:
    """Typed boundary for the storage scope capability."""

    name: str = "tenancy.storage_scope"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

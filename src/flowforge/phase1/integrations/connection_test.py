"""FlowForge Phase 1 integrations.connection_test component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ConnectionTestComponent:
    """Typed boundary for the connection test capability."""

    name: str = "integrations.connection_test"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

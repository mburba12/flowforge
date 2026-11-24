"""FlowForge Phase 1 integrations.connector component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ConnectorComponent:
    """Typed boundary for the connector capability."""

    name: str = "integrations.connector"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

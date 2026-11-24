"""FlowForge Phase 1 events.schema_registry component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SchemaRegistryComponent:
    """Typed boundary for the schema registry capability."""

    name: str = "events.schema_registry"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

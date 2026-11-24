"""FlowForge Phase 1 integrations.microsoft365 component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Microsoft365Component:
    """Typed boundary for the microsoft365 capability."""

    name: str = "integrations.microsoft365"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

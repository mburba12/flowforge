"""FlowForge Phase 1 operations.logging component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LoggingComponent:
    """Typed boundary for the logging capability."""

    name: str = "operations.logging"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

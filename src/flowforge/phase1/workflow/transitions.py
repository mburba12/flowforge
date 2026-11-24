"""FlowForge Phase 1 workflow.transitions component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TransitionsComponent:
    """Typed boundary for the transitions capability."""

    name: str = "workflow.transitions"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 operations.config_validation component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ConfigValidationComponent:
    """Typed boundary for the config validation capability."""

    name: str = "operations.config_validation"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

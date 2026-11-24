"""FlowForge Phase 1 identity.recovery_codes component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RecoveryCodesComponent:
    """Typed boundary for the recovery codes capability."""

    name: str = "identity.recovery_codes"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

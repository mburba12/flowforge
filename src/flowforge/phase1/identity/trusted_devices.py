"""FlowForge Phase 1 identity.trusted_devices component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TrustedDevicesComponent:
    """Typed boundary for the trusted devices capability."""

    name: str = "identity.trusted_devices"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

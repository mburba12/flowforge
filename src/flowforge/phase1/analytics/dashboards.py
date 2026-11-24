"""FlowForge Phase 1 analytics.dashboards component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DashboardsComponent:
    """Typed boundary for the dashboards capability."""

    name: str = "analytics.dashboards"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

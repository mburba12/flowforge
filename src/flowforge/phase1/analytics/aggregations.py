"""FlowForge Phase 1 analytics.aggregations component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AggregationsComponent:
    """Typed boundary for the aggregations capability."""

    name: str = "analytics.aggregations"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

"""FlowForge Phase 1 tenancy.query_scope component."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class QueryScopeComponent:
    """Typed boundary for the query scope capability."""

    name: str = "tenancy.query_scope"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"component": self.name, "accepted": True, "payload": payload}

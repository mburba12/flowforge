from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class UnifiedOpportunity:
    opportunity_id: str
    name: str
    stage: str
    amount: Decimal
    currency: str


class EngagementProvider(Protocol):
    code: str

    async def connect(self, authorization_code: str) -> tuple[str, str]: ...
    async def opportunities(
        self, organization_id: str, cursor: str | None
    ) -> tuple[list[UnifiedOpportunity], str | None]: ...
    async def verify_webhook(self, payload: bytes, signature: str) -> bool: ...

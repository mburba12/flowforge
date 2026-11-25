from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class UnifiedOrder:
    order_id: str
    order_number: str
    total: Decimal
    currency: str
    status: str
    placed_at: str


class CommerceProvider(Protocol):
    code: str

    async def connect(self, authorization_code: str) -> tuple[str, str]: ...
    async def orders(
        self, store_id: str, cursor: str | None
    ) -> tuple[list[UnifiedOrder], str | None]: ...
    async def verify_webhook(self, payload: bytes, signature: str) -> bool: ...

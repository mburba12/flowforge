from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class UnifiedFinanceDocument:
    document_id: str
    document_type: str
    number: str
    total: Decimal
    currency: str
    status: str
    document_date: str


class FinanceProvider(Protocol):
    code: str

    async def connect(self, authorization_code: str) -> tuple[str, str]: ...
    async def documents(
        self, organization_id: str, cursor: str | None
    ) -> tuple[list[UnifiedFinanceDocument], str | None]: ...
    async def verify_webhook(self, payload: bytes, signature: str) -> bool: ...

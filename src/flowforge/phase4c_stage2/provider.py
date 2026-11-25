from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderPayment:
    payment_id: str
    amount: Decimal
    currency: str
    status: str
    occurred_at: str
    method_type: str
    card_brand: str | None = None
    card_last4: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderPayout:
    payout_id: str
    gross: Decimal
    fees: Decimal
    net: Decimal
    currency: str
    arrival_at: str
    status: str


class PaymentProvider(Protocol):
    async def connect(self, authorization_code: str) -> tuple[str, str]: ...
    async def list_payments(self, account_reference: str) -> list[ProviderPayment]: ...
    async def list_payouts(self, account_reference: str) -> list[ProviderPayout]: ...
    async def verify_webhook(self, payload: bytes, signature: str) -> bool: ...

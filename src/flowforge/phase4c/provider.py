from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderAccount:
    account_id: str
    name: str
    mask: str | None
    account_type: str
    subtype: str | None
    currency: str
    current: Decimal | None
    available: Decimal | None


@dataclass(frozen=True, slots=True)
class ProviderTransaction:
    transaction_id: str
    account_id: str
    posted_at: str
    amount: Decimal
    currency: str
    description: str
    pending: bool = False
    removed: bool = False


class BankingProvider(Protocol):
    async def create_link_session(self, tenant_reference: str) -> str: ...
    async def exchange_token(self, public_token: str) -> tuple[str, str]: ...
    async def list_accounts(self, access_token: str) -> list[ProviderAccount]: ...
    async def sync_transactions(
        self, access_token: str, cursor: str | None
    ) -> tuple[list[ProviderTransaction], str | None]: ...
    async def revoke(self, access_token: str) -> None: ...

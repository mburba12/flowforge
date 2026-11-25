from decimal import Decimal

from .provider import ProviderAccount, ProviderTransaction


class SandboxBankingProvider:
    async def create_link_session(self, tenant_reference: str) -> str:
        return f"sandbox-link-{tenant_reference}"

    async def exchange_token(self, public_token: str) -> tuple[str, str]:
        if not public_token.startswith("sandbox-"):
            raise ValueError("Invalid sandbox public token")
        return "sandbox-access-token", "sandbox-item"

    async def list_accounts(self, access_token: str) -> list[ProviderAccount]:
        return [
            ProviderAccount(
                "sandbox-checking",
                "Operating Checking",
                "1842",
                "depository",
                "checking",
                "USD",
                Decimal("10000.00"),
                Decimal("9500.00"),
            )
        ]

    async def sync_transactions(
        self, access_token: str, cursor: str | None
    ) -> tuple[list[ProviderTransaction], str | None]:
        return [], cursor or "sandbox-cursor-1"

    async def revoke(self, access_token: str) -> None:
        return None

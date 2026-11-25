from datetime import UTC, datetime
from decimal import Decimal

from .provider import ProviderPayment, ProviderPayout


class SandboxStripeProvider:
    async def connect(self, authorization_code: str) -> tuple[str, str]:
        if not authorization_code.startswith("sandbox-"):
            raise ValueError("Invalid sandbox authorization code")
        return "acct_sandbox_stripe", "merchant_sandbox_stripe"

    async def list_payments(self, account_reference: str) -> list[ProviderPayment]:
        return [
            ProviderPayment(
                "pi_sandbox_001",
                Decimal("106.00"),
                "USD",
                "succeeded",
                datetime.now(UTC).isoformat(),
                "card",
                "visa",
                "4242",
            )
        ]

    async def list_payouts(self, account_reference: str) -> list[ProviderPayout]:
        return [
            ProviderPayout(
                "po_sandbox_001",
                Decimal("106.00"),
                Decimal("3.00"),
                Decimal("103.00"),
                "USD",
                datetime.now(UTC).isoformat(),
                "paid",
            )
        ]

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return signature == "sandbox-valid-signature"


class SandboxSquareProvider(SandboxStripeProvider):
    async def connect(self, authorization_code: str) -> tuple[str, str]:
        if not authorization_code.startswith("sandbox-"):
            raise ValueError("Invalid sandbox authorization code")
        return "square_sandbox_account", "square_sandbox_merchant"

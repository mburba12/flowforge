from decimal import Decimal

from .provider import UnifiedOpportunity


class SandboxEngagementProvider:
    def __init__(self, code: str):
        self.code = code

    async def connect(self, authorization_code: str) -> tuple[str, str]:
        if not authorization_code.startswith("sandbox-"):
            raise ValueError("Invalid sandbox authorization code")
        return (
            f"org_{self.code}_sandbox",
            f"{self.code.replace('_', ' ').title()} Sandbox",
        )

    async def opportunities(
        self, organization_id: str, cursor: str | None
    ) -> tuple[list[UnifiedOpportunity], str | None]:
        if cursor == "cursor_1":
            return [], "cursor_1"
        opportunity = UnifiedOpportunity(
            f"opportunity_{self.code}_001",
            f"{self.code.replace('_', ' ').title()} Sandbox Opportunity",
            "qualified",
            Decimal("5000.00"),
            "USD",
        )
        return [opportunity], "cursor_1"

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return signature == "sandbox-valid-signature"

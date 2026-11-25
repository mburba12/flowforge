from datetime import UTC, datetime
from decimal import Decimal

from .provider import UnifiedFinanceDocument


class SandboxFinanceProvider:
    def __init__(self, code: str):
        self.code = code

    async def connect(self, authorization_code: str) -> tuple[str, str]:
        if not authorization_code.startswith("sandbox-"):
            raise ValueError("Invalid sandbox authorization code")
        return f"org_{self.code}_sandbox", f"{self.code.replace('_', ' ').title()} Sandbox"

    async def documents(
        self, organization_id: str, cursor: str | None
    ) -> tuple[list[UnifiedFinanceDocument], str | None]:
        if cursor == "cursor_1":
            return [], "cursor_1"
        return [
            UnifiedFinanceDocument(
                f"doc_{self.code}_001",
                "invoice",
                f"{self.code[:4].upper()}-1001",
                Decimal("250.00"),
                "USD",
                "open",
                datetime.now(UTC).isoformat(),
            )
        ], "cursor_1"

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return signature == "sandbox-valid-signature"

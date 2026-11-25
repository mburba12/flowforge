from datetime import UTC, datetime
from decimal import Decimal

from .provider import UnifiedOrder


class SandboxCommerceProvider:
    def __init__(self, code: str):
        self.code = code

    async def connect(self, authorization_code: str) -> tuple[str, str]:
        if not authorization_code.startswith("sandbox-"):
            raise ValueError("Invalid sandbox authorization code")
        return f"store_{self.code}_sandbox", f"{self.code.replace('_', ' ').title()} Sandbox"

    async def orders(
        self, store_id: str, cursor: str | None
    ) -> tuple[list[UnifiedOrder], str | None]:
        order = UnifiedOrder(
            f"order_{self.code}_001",
            f"{self.code[:4].upper()}-1001",
            Decimal("129.95"),
            "USD",
            "paid",
            datetime.now(UTC).isoformat(),
        )
        return ([] if cursor == "cursor_1" else [order], "cursor_1")

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return signature == "sandbox-valid-signature"

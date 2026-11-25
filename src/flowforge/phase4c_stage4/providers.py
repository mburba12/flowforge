from datetime import UTC, datetime

from .provider import UnifiedTrackingEvent


class SandboxLogisticsProvider:
    def __init__(self, code: str):
        self.code = code

    async def connect(self, authorization_code: str) -> tuple[str, str]:
        if not authorization_code.startswith("sandbox-"):
            raise ValueError("Invalid sandbox authorization code")
        return f"account_{self.code}_sandbox", f"{self.code.replace('_', ' ').title()} Sandbox"

    async def tracking(
        self, account_id: str, cursor: str | None
    ) -> tuple[list[UnifiedTrackingEvent], str | None]:
        if cursor == "cursor_1":
            return [], "cursor_1"
        return [
            UnifiedTrackingEvent(
                f"event_{self.code}_001",
                "in_transit",
                "Shipment in transit",
                datetime.now(UTC).isoformat(),
            )
        ], "cursor_1"

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return signature == "sandbox-valid-signature"

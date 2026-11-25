from datetime import UTC, datetime
from decimal import Decimal

from .provider import UnifiedPayrollRun


class SandboxWorkforceProvider:
    def __init__(self, code: str):
        self.code = code

    async def connect(self, authorization_code: str) -> tuple[str, str]:
        if not authorization_code.startswith("sandbox-"):
            raise ValueError("Invalid sandbox authorization code")
        return (
            f"org_{self.code}_sandbox",
            f"{self.code.replace('_', ' ').title()} Sandbox",
        )

    async def payroll_runs(
        self, organization_id: str, cursor: str | None
    ) -> tuple[list[UnifiedPayrollRun], str | None]:
        if cursor == "cursor_1":
            return [], "cursor_1"
        run = UnifiedPayrollRun(
            f"payroll_{self.code}_001",
            Decimal("10000.00"),
            Decimal("7600.00"),
            "USD",
            "processed",
            datetime.now(UTC).date().isoformat(),
        )
        return [run], "cursor_1"

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return signature == "sandbox-valid-signature"

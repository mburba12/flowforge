from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class UnifiedPayrollRun:
    run_id: str
    gross_pay: Decimal
    net_pay: Decimal
    currency: str
    status: str
    pay_date: str


class WorkforceProvider(Protocol):
    code: str

    async def connect(self, authorization_code: str) -> tuple[str, str]: ...
    async def payroll_runs(
        self, organization_id: str, cursor: str | None
    ) -> tuple[list[UnifiedPayrollRun], str | None]: ...
    async def verify_webhook(self, payload: bytes, signature: str) -> bool: ...

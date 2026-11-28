from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CloseResult:
    period_id: str
    balanced: bool
    debits: Decimal
    credits: Decimal


def validate_close(
    period_id: str, debits: Decimal, credits: Decimal, open_exceptions: int
) -> CloseResult:
    if open_exceptions:
        raise ValueError("Open close exceptions remain")
    if debits != credits:
        raise ValueError("Trial balance is not balanced")
    return CloseResult(period_id, True, debits, credits)

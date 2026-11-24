from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MatchInput:
    ordered: Decimal
    received: Decimal
    invoiced: Decimal
    po_unit_price: Decimal
    invoice_unit_price: Decimal


@dataclass(frozen=True, slots=True)
class MatchPolicy:
    quantity_tolerance_bps: int = 0
    price_tolerance_bps: int = 100
    line_value_tolerance: Decimal = Decimal("5.00")


def evaluate(value: MatchInput, policy: MatchPolicy) -> tuple[str, list[str]]:
    reasons = []
    qbase = max(value.ordered, Decimal("1"))
    qvar = abs(value.invoiced - value.received) / qbase * 10000
    pbase = max(value.po_unit_price, Decimal("0.0001"))
    pvar = abs(value.invoice_unit_price - value.po_unit_price) / pbase * 10000
    if value.received <= 0:
        reasons.append("missing_receipt")
    if qvar > policy.quantity_tolerance_bps:
        reasons.append("quantity_variance")
    if (
        pvar > policy.price_tolerance_bps
        and abs((value.invoice_unit_price - value.po_unit_price) * value.invoiced)
        > policy.line_value_tolerance
    ):
        reasons.append("price_variance")
    return ("matched" if not reasons else "exception", reasons)

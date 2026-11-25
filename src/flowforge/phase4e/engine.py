from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    expected: Decimal
    actual: Decimal
    difference: Decimal
    within_tolerance: bool
    severity: Severity
    evidence: tuple[str, ...]


def reconcile_amount(
    expected: Decimal, actual: Decimal, tolerance: Decimal, evidence: tuple[str, ...]
) -> ReconciliationResult:
    difference = actual - expected
    absolute = abs(difference)
    if absolute == 0:
        severity = Severity.LOW
    elif absolute <= tolerance:
        severity = Severity.MEDIUM
    elif absolute >= Decimal(10000):
        severity = Severity.CRITICAL
    else:
        severity = Severity.HIGH
    return ReconciliationResult(
        expected, actual, difference, absolute <= tolerance, severity, evidence
    )


def commerce_to_cash(
    order_total: Decimal,
    captured: Decimal,
    settled: Decimal,
    deposited: Decimal,
    tolerance: Decimal,
) -> tuple[ReconciliationResult, ...]:
    return (
        reconcile_amount(order_total, captured, tolerance, ("order", "capture")),
        reconcile_amount(captured, settled, tolerance, ("capture", "settlement")),
        reconcile_amount(settled, deposited, tolerance, ("settlement", "deposit")),
    )


def three_way_match(
    ordered_qty: Decimal, received_qty: Decimal, billed_qty: Decimal, tolerance: Decimal
) -> tuple[ReconciliationResult, ReconciliationResult]:
    return (
        reconcile_amount(ordered_qty, received_qty, tolerance, ("purchase_order", "receipt")),
        reconcile_amount(received_qty, billed_qty, tolerance, ("receipt", "supplier_bill")),
    )


def payroll_to_funding(
    payroll_net: Decimal, ledger_net: Decimal, funded: Decimal, tolerance: Decimal
) -> tuple[ReconciliationResult, ReconciliationResult]:
    return (
        reconcile_amount(payroll_net, ledger_net, tolerance, ("payroll", "ledger")),
        reconcile_amount(payroll_net, funded, tolerance, ("payroll", "bank_funding")),
    )


def available_to_promise(
    on_hand: Decimal, reserved: Decimal, inbound_confirmed: Decimal
) -> Decimal:
    return on_hand - reserved + inbound_confirmed

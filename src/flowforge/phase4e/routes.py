from fastapi import APIRouter

from .engine import ReconciliationResult, commerce_to_cash, reconcile_amount
from .schemas import AmountReconciliationRequest, CommerceToCashRequest

router = APIRouter(prefix="/api/v4/reconciliations", tags=["phase4e-reconciliation"])


def _result(row: ReconciliationResult) -> dict[str, object]:
    return {
        "expected": str(row.expected),
        "actual": str(row.actual),
        "difference": str(row.difference),
        "within_tolerance": row.within_tolerance,
        "severity": row.severity,
        "evidence": row.evidence,
    }


@router.post("/amount")
async def amount(body: AmountReconciliationRequest) -> dict[str, object]:
    return _result(
        reconcile_amount(body.expected, body.actual, body.tolerance, tuple(body.evidence))
    )


@router.post("/commerce-to-cash")
async def commerce(body: CommerceToCashRequest) -> dict[str, object]:
    results = commerce_to_cash(
        body.order_total, body.captured, body.settled, body.deposited, body.tolerance
    )
    return {
        "results": [_result(row) for row in results],
        "balanced": all(row.within_tolerance for row in results),
    }

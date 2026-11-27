"""Payroll setup shared by the payroll and tax workflow tests."""

from dataclasses import dataclass
from decimal import Decimal

from .conftest import PERIOD_START, Harness

# Worker inputs and the hand-computed expected results.
HOURLY_RATE = "30.00"
WORKER_INPUT = {
    "regular_hours": "80",
    "overtime_hours": "4",
    "bonus": "100.00",
    "pretax_deductions": "50.00",
    "posttax_deductions": "20.00",
    "employee_tax_rate": "0.10",
    "employer_tax_rate": "0.0765",
}
# gross = 80*30 + 4*30*1.5 + 100 = 2680.00; taxable = 2630.00
# employee tax = 263.00; employer tax = 2630 * 0.0765 = 201.195 -> 201.20 (half up)
# net = 2680 - 50 - 263 - 20 = 2347.00
EXPECTED = {
    "gross": Decimal("2680.00"),
    "employee_tax": Decimal("263.00"),
    "employer_tax": Decimal("201.20"),
    "deductions": Decimal("70.00"),
    "net": Decimal("2347.00"),
}


@dataclass
class PayrollRun:
    run_id: str
    worker_id: str
    payroll_worker_id: str


def post_accounts(h: Harness) -> dict[str, str]:
    return {
        "wage_expense_account_id": h.accounts["wages"],
        "employer_tax_expense_account_id": h.accounts["employer_tax_expense"],
        "employee_tax_payable_account_id": h.accounts["employee_tax_payable"],
        "employer_tax_payable_account_id": h.accounts["employer_tax_payable"],
        "deductions_payable_account_id": h.accounts["deductions_payable"],
        "net_pay_payable_account_id": h.accounts["net_pay_payable"],
        "currency_code": "USD",
    }


async def worker(h: Harness) -> str:
    party = await h.person("Dana", "Rivera")
    created = await h.post(
        "/api/v4a/workers",
        json={
            "party_id": party,
            "worker_type": "employee",
            "hire_date": "2025-06-01",
            "default_currency": "USD",
            "pay_frequency": "semimonthly",
        },
    )
    worker_id = str(created["id"])
    await h.post(
        f"/api/v4a/workers/{worker_id}/compensation",
        json={
            "compensation_type": "hourly",
            "amount": HOURLY_RATE,
            "currency_code": "USD",
            "effective_from": "2025-06-01",
        },
    )
    return worker_id


async def draft_run(h: Harness, period_code: str = "2026-01A") -> str:
    group = await h.post(
        "/api/v4a/pay-groups",
        json={
            "code": f"SM-{period_code}",
            "name": "Semimonthly",
            "pay_frequency": "semimonthly",
            "currency_code": "USD",
        },
    )
    period = await h.post(
        "/api/v4a/pay-periods",
        json={
            "pay_group_id": group["id"],
            "period_code": period_code,
            "start_date": PERIOD_START.isoformat(),
            "end_date": "2026-01-15",
            "pay_date": "2026-01-20",
        },
    )
    run = await h.post(
        "/api/v4a/payroll/runs",
        json={
            "pay_group_id": group["id"],
            "pay_period_id": period["id"],
            "ledger_id": h.ledger_id,
            "accounting_period_id": h.period_id,
        },
    )
    assert run["status"] == "draft"
    return str(run["id"])


async def approved_run(h: Harness) -> PayrollRun:
    worker_id = await worker(h)
    run_id = await draft_run(h)
    await h.post(
        f"/api/v4a/payroll/runs/{run_id}/calculate",
        json={"workers": [{"worker_id": worker_id, **WORKER_INPUT}]},
    )
    await h.post(f"/api/v4a/payroll/runs/{run_id}/approve", as_approver=True)
    rows = await h.sql("SELECT id FROM payroll_run_workers WHERE payroll_run_id = :r", r=run_id)
    return PayrollRun(run_id=run_id, worker_id=worker_id, payroll_worker_id=str(rows[0][0]))


async def posted_run(h: Harness) -> PayrollRun:
    run = await approved_run(h)
    await h.post(f"/api/v4a/payroll/runs/{run.run_id}/post", json=post_accounts(h))
    return run

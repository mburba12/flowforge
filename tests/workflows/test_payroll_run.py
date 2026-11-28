"""Payroll release workflow: worker -> run -> calculate -> approve -> post -> pay -> reconcile."""

from decimal import Decimal

from . import payroll_helpers as ph
from .conftest import Harness


async def test_payroll_gross_to_net_to_gl(harness: Harness) -> None:
    h = harness
    worker_id = await ph.worker(h)
    run_id = await ph.draft_run(h)

    # Negative net pay is rejected and leaves the run in draft.
    await h.post(
        f"/api/v4a/payroll/runs/{run_id}/calculate",
        json={
            "workers": [{**ph.WORKER_INPUT, "worker_id": worker_id, "posttax_deductions": "9999"}]
        },
        expect=409,
    )
    calc = await h.post(
        f"/api/v4a/payroll/runs/{run_id}/calculate",
        json={"workers": [{"worker_id": worker_id, **ph.WORKER_INPUT}]},
    )
    assert calc["status"] == "calculated"
    await h.post(
        f"/api/v4a/payroll/runs/{run_id}/calculate",
        json={"workers": [{"worker_id": worker_id, **ph.WORKER_INPUT}]},
        expect=409,
    )  # a calculated run cannot be recalculated

    rows = await h.sql(
        "SELECT gross_pay, employee_taxes, employer_taxes, pretax_deductions + posttax_deductions,"
        " net_pay FROM payroll_run_workers WHERE payroll_run_id = :r",
        r=run_id,
    )
    assert len(rows) == 1
    gross, ee_tax, er_tax, deductions, net = (Decimal(x) for x in rows[0])
    assert (gross, ee_tax, er_tax, deductions, net) == (
        ph.EXPECTED["gross"],
        ph.EXPECTED["employee_tax"],
        ph.EXPECTED["employer_tax"],
        ph.EXPECTED["deductions"],
        ph.EXPECTED["net"],
    )

    # Approval controls.
    await h.post(f"/api/v4a/payroll/runs/{run_id}/post", json=ph.post_accounts(h), expect=409)
    await h.require_two_people()
    await h.post(f"/api/v4a/payroll/runs/{run_id}/approve", expect=409)  # creator
    approved = await h.post(f"/api/v4a/payroll/runs/{run_id}/approve", as_approver=True)
    assert approved["status"] == "approved"

    # Posting (once).
    posted = await h.post(f"/api/v4a/payroll/runs/{run_id}/post", json=ph.post_accounts(h))
    assert posted["status"] == "posted"
    await h.post(f"/api/v4a/payroll/runs/{run_id}/post", json=ph.post_accounts(h), expect=409)

    await h.assert_ledger_integrity()
    assert await h.account_balance("wages") == ph.EXPECTED["gross"]
    assert await h.account_balance("employer_tax_expense") == ph.EXPECTED["employer_tax"]
    assert await h.account_balance("employee_tax_payable") == -ph.EXPECTED["employee_tax"]
    assert await h.account_balance("employer_tax_payable") == -ph.EXPECTED["employer_tax"]
    assert await h.account_balance("deductions_payable") == -ph.EXPECTED["deductions"]
    assert await h.account_balance("net_pay_payable") == -ph.EXPECTED["net"]

    # Pay the worker their net pay.
    paid = await h.post(
        f"/api/v4a/payroll/runs/{run_id}/payments",
        json={
            "worker_id": worker_id,
            "cash_account_id": h.accounts["cash"],
            "net_pay_payable_account_id": h.accounts["net_pay_payable"],
            "amount": str(ph.EXPECTED["net"]),
            "currency_code": "USD",
        },
    )
    assert paid["status"] == "paid"
    await h.assert_ledger_integrity()
    assert await h.account_balance("net_pay_payable") == Decimal("0.00")
    assert await h.account_balance("cash") == -ph.EXPECTED["net"]

    recon = await h.post(f"/api/v4a/payroll/runs/{run_id}/reconcile")
    assert recon["status"] == "reconciled", recon


async def test_payroll_post_rejected_in_closed_period(harness: Harness) -> None:
    h = harness
    run = await ph.approved_run(h)
    await h.close_period()
    await h.post(f"/api/v4a/payroll/runs/{run.run_id}/post", json=ph.post_accounts(h), expect=409)
    assert await h.sql("SELECT 1 FROM journal_entries") == [], "no journal may be written"


async def test_payroll_calculation_is_reproducible(harness: Harness) -> None:
    h = harness
    worker_id = await ph.worker(h)
    results = []
    for code in ("2026-01A", "2026-01B"):
        run_id = await ph.draft_run(h, period_code=code)
        await h.post(
            f"/api/v4a/payroll/runs/{run_id}/calculate",
            json={"workers": [{"worker_id": worker_id, **ph.WORKER_INPUT}]},
        )
        rows = await h.sql(
            "SELECT gross_pay, employee_taxes, employer_taxes, net_pay FROM payroll_run_workers"
            " WHERE payroll_run_id = :r",
            r=run_id,
        )
        results.append(tuple(Decimal(x) for x in rows[0]))
    assert results[0] == results[1]


async def test_payroll_payment_cannot_exceed_net_pay(harness: Harness) -> None:
    h = harness
    run = await ph.posted_run(h)
    payment = {
        "worker_id": run.worker_id,
        "cash_account_id": h.accounts["cash"],
        "net_pay_payable_account_id": h.accounts["net_pay_payable"],
        "amount": str(ph.EXPECTED["net"]),
        "currency_code": "USD",
    }
    await h.post(f"/api/v4a/payroll/runs/{run.run_id}/payments", json=payment)
    liability = await h.sql(
        "SELECT open_amount FROM payroll_liabilities WHERE payroll_run_id = :r"
        " AND liability_type = 'net_pay'",
        r=run.run_id,
    )
    assert Decimal(liability[0][0]) == Decimal("0.00"), "net-pay liability was not settled"
    await h.post(f"/api/v4a/payroll/runs/{run.run_id}/payments", json=payment, expect=409)

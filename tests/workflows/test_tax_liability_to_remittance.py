"""Tax release workflow: rule -> calculation -> liability -> return -> remit -> reconcile."""

from decimal import Decimal

from . import payroll_helpers as ph
from .conftest import IN_PERIOD, Harness


async def _rule(h: Harness) -> tuple[str, str]:
    jurisdiction = await h.post(
        "/api/v4b/jurisdictions",
        json={
            "code": "US-FED",
            "name": "United States Federal",
            "level": "federal",
            "country_code": "US",
        },
    )
    rule = await h.post(
        "/api/v4b/tax-rules",
        json={
            "jurisdiction_id": jurisdiction["id"],
            "code": "OASDI-EE",
            "responsibility": "employee",
            "rate": "0.062",
            "annual_wage_base": "168600",
            "effective_from": "2026-01-01",
        },
    )
    return str(jurisdiction["id"]), str(rule["id"])


async def test_tax_calculation_rules(harness: Harness) -> None:
    h = harness
    run = await ph.approved_run(h)
    _, rule_id = await _rule(h)

    def calc(wages: str, **extra: object) -> dict[str, object]:
        return {
            "payroll_worker_id": run.payroll_worker_id,
            "tax_rule_id": rule_id,
            "taxable_wages": wages,
            **extra,
        }

    basic = await h.post("/api/v4b/calculate", json=calc("1000.00"))
    assert (Decimal(basic["employee_amount"]), Decimal(basic["employer_amount"])) == (
        Decimal("62.00"),
        Decimal("0"),
    )
    capped = await h.post("/api/v4b/calculate", json=calc("200000.00"))
    assert Decimal(capped["employee_amount"]) == Decimal("10453.20")  # 168600 * 0.062
    extra = await h.post("/api/v4b/calculate", json=calc("1000.00", additional_withholding="25.00"))
    assert Decimal(extra["employee_amount"]) == Decimal("87.00")
    exempt = await h.post("/api/v4b/calculate", json=calc("1000.00", exempt=True))
    assert Decimal(exempt["employee_amount"]) == Decimal("0")

    await h.post(
        "/api/v4b/tax-rules",
        json={
            "jurisdiction_id": "00000000-0000-0000-0000-000000000000",
            "code": "BAD",
            "responsibility": "employee",
            "rate": "0.01",
            "effective_from": "2026-01-01",
        },
        expect=404,
    )


async def test_tax_liability_return_remittance(harness: Harness) -> None:
    h = harness
    run = await ph.posted_run(h)  # credits employee tax payable 263.00
    jurisdiction_id, _ = await _rule(h)
    authority_id = await h.tax_authority(jurisdiction_id, "IRS")
    tax_account = h.accounts["employee_tax_payable"]

    liability = await h.post(
        "/api/v4b/liabilities",
        json={
            "authority_id": authority_id,
            "payroll_run_id": run.run_id,
            "liability_type": "employee_tax",
            "amount": str(ph.EXPECTED["employee_tax"]),
            "due_date": "2026-02-15",
        },
    )
    assert Decimal(liability["open_amount"]) == ph.EXPECTED["employee_tax"]

    before = await h.post(
        "/api/v4b/reconcile",
        params={"authority_id": authority_id, "tax_payable_account_id": tax_account},
    )
    assert before["status"] == "reconciled", before

    tax_return = await h.post(
        "/api/v4b/returns",
        json={
            "authority_id": authority_id,
            "period_code": "2026-01",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "due_date": "2026-02-15",
            "taxable_wages": "2630.00",
            "tax_amount": str(ph.EXPECTED["employee_tax"]),
            "tax_code": "OASDI-EE",
        },
    )
    return_id = tax_return["id"]

    def remit(amount: str) -> dict[str, str]:
        return {
            "liability_id": liability["id"],
            "payment_date": IN_PERIOD.isoformat(),
            "amount": amount,
            "ledger_id": h.ledger_id,
            "accounting_period_id": h.period_id,
            "tax_payable_account_id": tax_account,
            "cash_account_id": h.accounts["cash"],
            "currency_code": "USD",
        }

    await h.post(f"/api/v4b/returns/{return_id}/remit", json=remit("263.00"), expect=409)  # draft
    await h.post(f"/api/v4b/returns/{return_id}/approve", expect=409)  # creator
    approved = await h.post(f"/api/v4b/returns/{return_id}/approve", as_approver=True)
    assert approved["status"] == "approved"

    await h.post(f"/api/v4b/returns/{return_id}/remit", json=remit("263.01"), expect=409)
    remitted = await h.post(f"/api/v4b/returns/{return_id}/remit", json=remit("263.00"))
    assert Decimal(remitted["amount"]) == Decimal("263.00")
    await h.post(f"/api/v4b/returns/{return_id}/remit", json=remit("0.01"), expect=409)

    state = await h.sql(
        "SELECT open_amount, status FROM tax_liabilities WHERE id = :i", i=liability["id"]
    )
    assert (Decimal(state[0][0]), state[0][1]) == (Decimal("0.00"), "paid")

    await h.assert_ledger_integrity()
    assert await h.account_balance("employee_tax_payable") == Decimal("0.00")

    after = await h.post(
        "/api/v4b/reconcile",
        params={"authority_id": authority_id, "tax_payable_account_id": tax_account},
    )
    assert after["status"] == "reconciled", after
    assert Decimal(after["subledger_total"]) == Decimal(after["gl_total"]) == Decimal("0")


async def test_tax_remittance_rejected_in_closed_period(harness: Harness) -> None:
    h = harness
    run = await ph.approved_run(h)
    jurisdiction_id, _ = await _rule(h)
    authority_id = await h.tax_authority(jurisdiction_id, "IRS")
    liability = await h.post(
        "/api/v4b/liabilities",
        json={
            "authority_id": authority_id,
            "payroll_run_id": run.run_id,
            "liability_type": "employee_tax",
            "amount": "100.00",
            "due_date": "2026-02-15",
        },
    )
    tax_return = await h.post(
        "/api/v4b/returns",
        json={
            "authority_id": authority_id,
            "period_code": "2026-01",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "due_date": "2026-02-15",
            "taxable_wages": "1000.00",
            "tax_amount": "100.00",
            "tax_code": "OASDI-EE",
        },
    )
    await h.post(f"/api/v4b/returns/{tax_return['id']}/approve", as_approver=True)
    await h.close_period()
    await h.post(
        f"/api/v4b/returns/{tax_return['id']}/remit",
        json={
            "liability_id": liability["id"],
            "payment_date": IN_PERIOD.isoformat(),
            "amount": "100.00",
            "ledger_id": h.ledger_id,
            "accounting_period_id": h.period_id,
            "tax_payable_account_id": h.accounts["employee_tax_payable"],
            "cash_account_id": h.accounts["cash"],
            "currency_code": "USD",
        },
        expect=409,
    )
    assert await h.sql("SELECT 1 FROM journal_entries") == [], "no journal may be written"
    state = await h.sql("SELECT open_amount FROM tax_liabilities WHERE id = :i", i=liability["id"])
    assert Decimal(state[0][0]) == Decimal("100.00")

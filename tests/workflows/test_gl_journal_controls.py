"""General-ledger manual journal controls under RLS (shared posting rules)."""

from decimal import Decimal

from .conftest import IN_PERIOD, Harness


def _journal(h: Harness, debit: str, credit: str, on: str = "") -> dict[str, object]:
    return {
        "ledger_id": h.ledger_id,
        "period_id": h.period_id,
        "journal_date": on or IN_PERIOD.isoformat(),
        "description": "Owner contribution",
        "lines": [
            {
                "account_id": h.accounts["cash"],
                "debit": debit,
                "credit": "0",
                "currency_code": "USD",
            },
            {
                "account_id": h.accounts["equity"],
                "debit": "0",
                "credit": credit,
                "currency_code": "USD",
            },
        ],
    }


async def test_gl_journal_approve_post_and_trial_balance(harness: Harness) -> None:
    h = harness
    await h.post("/api/v2/journals", json=_journal(h, "100.00", "90.00"), expect=422)
    journal = await h.post("/api/v2/journals", json=_journal(h, "100.00", "100.00"))
    await h.post(f"/api/v2/journals/{journal['id']}/post", expect=409)  # not approved
    await h.post(f"/api/v2/journals/{journal['id']}/approve", expect=409)  # creator
    await h.post(f"/api/v2/journals/{journal['id']}/approve", as_approver=True)
    posted = await h.post(f"/api/v2/journals/{journal['id']}/post", as_approver=True)
    assert posted["status"] == "posted"
    await h.post(f"/api/v2/journals/{journal['id']}/post", as_approver=True, expect=409)
    await h.assert_ledger_integrity()
    assert await h.trial_balance() == (Decimal("100.00"), Decimal("100.00"))


async def test_gl_post_rejected_in_closed_period(harness: Harness) -> None:
    h = harness
    pending = await h.post("/api/v2/journals", json=_journal(h, "50.00", "50.00"))
    await h.post(f"/api/v2/journals/{pending['id']}/approve", as_approver=True)
    # An approved but unposted journal blocks closing the period.
    await h.post(f"/api/v2/accounting-periods/{h.period_id}/close", expect=409)
    await h.post(f"/api/v2/journals/{pending['id']}/post", as_approver=True)
    await h.close_period()
    late = await h.post("/api/v2/journals", json=_journal(h, "20.00", "20.00"))
    await h.post(f"/api/v2/journals/{late['id']}/approve", as_approver=True)
    await h.post(f"/api/v2/journals/{late['id']}/post", as_approver=True, expect=409)
    assert await h.trial_balance() == (Decimal("50.00"), Decimal("50.00"))


async def test_gl_post_rejected_outside_period_dates(harness: Harness) -> None:
    h = harness
    journal = await h.post("/api/v2/journals", json=_journal(h, "50.00", "50.00", on="2026-03-01"))
    await h.post(f"/api/v2/journals/{journal['id']}/approve", as_approver=True)
    await h.post(f"/api/v2/journals/{journal['id']}/post", as_approver=True, expect=409)


async def test_gl_journal_refuses_accounts_outside_the_ledger(harness: Harness) -> None:
    from uuid import uuid4

    h = harness
    foreign = _journal(h, "10.00", "10.00")
    foreign["lines"][0]["account_id"] = str(uuid4())  # type: ignore[index]
    # Refused when the journal is created, not later when someone tries to post it.
    await h.post("/api/v2/journals", json=foreign, expect=409)
    rows = await h.sql("SELECT count(*) FROM journal_entries WHERE tenant_id = :t", t=h.tenant_id)
    assert rows[0][0] == 0

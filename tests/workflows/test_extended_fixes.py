"""Regression tests for defects found by the functional audit (extended domains)."""

from uuid import uuid4

from .conftest import IN_PERIOD, Harness
from .payroll_helpers import worker


async def test_lead_converts_to_an_organization_or_a_person(harness: Harness) -> None:
    h = harness
    for company in ("Acme Supplies", None):
        lead = await h.post(
            "/api/v2/crm/leads",
            json={
                "lead_number": f"L-{uuid4().hex[:6]}",
                "contact_name": "Pat Example",
                "company_name": company,
            },
        )
        converted = await h.post(f"/api/v2/crm/leads/{lead['id']}/convert")
        kind = await h.sql("SELECT kind FROM parties WHERE id = :p", p=converted["party_id"])
        assert kind[0][0] == ("organization" if company else "person")
        await h.post(f"/api/v2/crm/leads/{lead['id']}/convert", expect=409)  # only once


async def test_open_ended_assignment_and_overlap(harness: Harness) -> None:
    h = harness
    worker_id = await worker(h)
    body = {
        "worker_id": worker_id,
        "employment_type": "full_time",
        "effective_from": IN_PERIOD.isoformat(),
    }
    await h.post("/api/v2/workforce/completion/assignments", json=body, expect=201)
    # A second open-ended assignment overlaps the first.
    await h.post("/api/v2/workforce/completion/assignments", json=body, expect=409)


async def test_recurring_journal_posts_a_numbered_balanced_journal(harness: Harness) -> None:
    h = harness
    recurring = await h.post(
        "/api/v2/finance/advanced/recurring-journals",
        json={
            "code": f"RENT-{uuid4().hex[:4]}",
            "description": "Monthly rent",
            "ledger_id": h.ledger_id,
            "frequency": "monthly",
            "next_run_date": IN_PERIOD.isoformat(),
            "debit_account_id": h.accounts["expense"],
            "credit_account_id": h.accounts["cash"],
            "amount": "250.00",
        },
    )
    posted = await h.post(
        f"/api/v2/finance/final/recurring/{recurring['id']}/post",
        json={
            "idempotency_key": uuid4().hex,
            "journal_date": IN_PERIOD.isoformat(),
            "period_id": h.period_id,
        },
    )
    rows = await h.sql(
        "SELECT j.journal_number, count(l.id), sum(l.debit), sum(l.credit) FROM journal_entries j"
        " JOIN journal_lines l ON l.journal_id = j.id WHERE j.id = :j GROUP BY j.journal_number",
        j=posted["journal_id"],
    )
    number, lines, debit, credit = rows[0]
    assert number and lines == 2 and debit == credit == 250

"""Release-completion APIs: period close/reopen, tax authorities, payroll-derived liabilities,
tax effective dating, order status history, open items and aging, payroll and tax reads."""

from decimal import Decimal

from . import payroll_helpers as ph
from .conftest import IN_PERIOD, Harness
from .test_ap_procure_to_pay import _approved_po, _invoice, _post_params, _vendor
from .test_ar_order_to_cash import _customer, _order, _stocked_product


def _journal(h: Harness) -> dict[str, object]:
    return {
        "ledger_id": h.ledger_id,
        "period_id": h.period_id,
        "journal_date": IN_PERIOD.isoformat(),
        "description": "Close test",
        "lines": [
            {
                "account_id": h.accounts["cash"],
                "debit": "5.00",
                "credit": "0",
                "currency_code": "USD",
            },
            {
                "account_id": h.accounts["equity"],
                "debit": "0",
                "credit": "5.00",
                "currency_code": "USD",
            },
        ],
    }


async def test_period_close_and_reopen(harness: Harness) -> None:
    h = harness
    journal = await h.post("/api/v2/journals", json=_journal(h))
    await h.post(f"/api/v2/journals/{journal['id']}/approve", as_approver=True)
    await h.post(f"/api/v2/accounting-periods/{h.period_id}/close", expect=409)  # unposted
    await h.post(f"/api/v2/journals/{journal['id']}/post", as_approver=True)
    closed = await h.post(f"/api/v2/accounting-periods/{h.period_id}/close")
    assert closed["status"] == "closed"
    await h.post(f"/api/v2/accounting-periods/{h.period_id}/close", expect=409)
    late = await h.post("/api/v2/journals", json=_journal(h))
    await h.post(f"/api/v2/journals/{late['id']}/approve", as_approver=True)
    await h.post(f"/api/v2/journals/{late['id']}/post", as_approver=True, expect=409)
    await h.post(
        f"/api/v2/accounting-periods/{h.period_id}/reopen", json={"reason": "no"}, expect=422
    )
    reopened = await h.post(
        f"/api/v2/accounting-periods/{h.period_id}/reopen",
        json={"reason": "Late supplier invoice received"},
    )
    assert reopened["status"] == "open"
    await h.post(f"/api/v2/journals/{late['id']}/post", as_approver=True)
    periods = await h.call("GET", "/api/v2/accounting-periods")
    assert [p["status"] for p in periods] == ["open"]
    actions = [
        r[0]
        for r in await h.sql(
            "SELECT action FROM audit_entries WHERE resource_type = 'accounting_period'"
            " ORDER BY occurred_at"
        )
    ]
    assert actions == ["closed", "reopened"]


async def test_tax_authorities(harness: Harness) -> None:
    h = harness
    jurisdiction = await h.post(
        "/api/v4b/jurisdictions",
        json={"code": "US-TX", "name": "Texas", "level": "state", "country_code": "US"},
    )
    authority = await h.tax_authority(jurisdiction["id"], "TX-TWC")
    await h.post(
        "/api/v4b/authorities",
        json={"jurisdiction_id": jurisdiction["id"], "code": "TX-TWC", "name": "Duplicate"},
        expect=409,
    )
    await h.post(
        "/api/v4b/authorities",
        json={
            "jurisdiction_id": "00000000-0000-0000-0000-000000000000",
            "code": "X",
            "name": "Unknown",
        },
        expect=404,
    )
    listed = await h.call("GET", "/api/v4b/authorities")
    assert [a["id"] for a in listed] == [authority]


async def test_liabilities_from_posted_payroll(harness: Harness) -> None:
    h = harness
    draft_only = await ph.approved_run(h)
    jurisdiction = await h.post(
        "/api/v4b/jurisdictions",
        json={"code": "US-FED", "name": "Federal", "level": "federal", "country_code": "US"},
    )
    authority = await h.tax_authority(jurisdiction["id"], "IRS")
    body = {
        "payroll_run_id": draft_only.run_id,
        "authority_id": authority,
        "due_date": "2026-02-15",
    }
    await h.post("/api/v4b/liabilities/from-payroll", json=body, expect=409)  # not posted
    await h.post(f"/api/v4a/payroll/runs/{draft_only.run_id}/post", json=ph.post_accounts(h))
    created = await h.post("/api/v4b/liabilities/from-payroll", json=body)
    amounts = {x["liability_type"]: Decimal(x["amount"]) for x in created}
    assert amounts == {
        "employee_tax": ph.EXPECTED["employee_tax"],
        "employer_tax": ph.EXPECTED["employer_tax"],
    }
    await h.post("/api/v4b/liabilities/from-payroll", json=body, expect=409)  # once only
    listed = await h.call("GET", "/api/v4b/liabilities")
    assert len(listed) == 2
    recon = await h.post(
        "/api/v4b/reconcile",
        params={
            "authority_id": authority,
            "tax_payable_account_id": h.accounts["employee_tax_payable"],
        },
    )
    assert Decimal(recon["gl_total"]) == ph.EXPECTED["employee_tax"]


async def test_tax_rule_effective_dating(harness: Harness) -> None:
    h = harness
    run = await ph.approved_run(h)
    jurisdiction = await h.post(
        "/api/v4b/jurisdictions",
        json={"code": "US-FED", "name": "Federal", "level": "federal", "country_code": "US"},
    )
    future = await h.post(
        "/api/v4b/tax-rules",
        json={
            "jurisdiction_id": jurisdiction["id"],
            "code": "FUTA",
            "responsibility": "employer",
            "rate": "0.006",
            "effective_from": "2027-01-01",
        },
    )
    ended = await h.post(
        "/api/v4b/tax-rules",
        json={
            "jurisdiction_id": jurisdiction["id"],
            "code": "OLD",
            "responsibility": "employee",
            "rate": "0.01",
            "effective_from": "2020-01-01",
            "effective_to": "2025-12-31",
        },
    )

    def calc(rule_id: str, as_of: str) -> dict[str, str]:
        return {
            "payroll_worker_id": run.payroll_worker_id,
            "tax_rule_id": rule_id,
            "taxable_wages": "1000.00",
            "as_of": as_of,
        }

    await h.post("/api/v4b/calculate", json=calc(future["id"], "2026-06-01"), expect=409)
    ok = await h.post("/api/v4b/calculate", json=calc(future["id"], "2027-02-01"))
    assert Decimal(ok["employer_amount"]) == Decimal("6.00")
    await h.post("/api/v4b/calculate", json=calc(ended["id"], "2026-01-15"), expect=409)
    old = await h.post("/api/v4b/calculate", json=calc(ended["id"], "2025-06-30"))
    assert Decimal(old["employee_amount"]) == Decimal("10.00")


async def test_order_status_history_and_ar_aging(harness: Harness) -> None:
    h = harness
    customer_id = await _customer(h, "History Retail", "10000")
    held_id = await _customer(h, "Held Retail", "10")
    product_id, _, _ = await _stocked_product(h)
    order = await _order(h, customer_id, product_id, "20")
    await h.post(f"/api/v3b/orders/{order['id']}/reserve")
    await h.post(
        f"/api/v3b/orders/{order['id']}/ship-invoice",
        params={"ship_date": IN_PERIOD.isoformat(), "due_date": "2026-02-14"},
    )
    held = await _order(h, held_id, product_id, "5")

    detail = await h.call("GET", f"/api/v3b/orders/{order['id']}")
    assert detail["status"] == "invoiced"
    assert [e["status"] for e in detail["status_history"]] == ["approved", "reserved", "invoiced"]
    assert len(detail["shipments"]) == 1 and len(detail["invoices"]) == 1
    assert detail["lines"][0]["shipped"].startswith("20")
    held_detail = await h.call("GET", f"/api/v3b/orders/{held['id']}")
    assert [e["status"] for e in held_detail["status_history"]] == ["credit_hold"]
    invoiced = await h.call("GET", "/api/v3b/orders", params={"status": "invoiced"})
    assert [o["id"] for o in invoiced] == [order["id"]]

    open_items = await h.call("GET", "/api/v3b/open-items")
    assert [Decimal(x["open_amount"]) for x in open_items] == [Decimal("200.00")]
    early = await h.call("GET", "/api/v3b/aging", params={"as_of": "2026-02-10"})
    assert early["buckets"]["current"] == "200.00"
    late = await h.call("GET", "/api/v3b/aging", params={"as_of": "2026-03-20"})
    assert late["buckets"]["31-60"] == "200.00" and late["buckets"]["current"] == "0.00"
    assert Decimal(late["total_open"]) == await h.account_balance("ar"), "aging != AR control"


async def test_ap_open_items_and_aging(harness: Harness) -> None:
    h = harness
    vendor_id = await _vendor(h)
    po_id, lines = await _approved_po(h, vendor_id)
    await h.post(
        "/api/v3/goods-receipts",
        json={
            "purchase_order_id": po_id,
            "receipt_date": IN_PERIOD.isoformat(),
            "lines": [
                {"po_line_id": lines[0], "quantity": "10"},
                {"po_line_id": lines[1], "quantity": "4"},
            ],
        },
    )
    invoice_id = await _invoice(h, vendor_id, po_id, lines, "INV-AGING")
    await h.post(f"/api/v3/vendor-invoices/{invoice_id}/match")
    await h.post(f"/api/v3/vendor-invoices/{invoice_id}/post", params=_post_params(h))
    items = await h.call("GET", "/api/v3/open-items")
    assert [Decimal(x["open_amount"]) for x in items] == [Decimal("300.00")]
    aging = await h.call("GET", "/api/v3/aging", params={"as_of": "2026-05-20"})
    assert aging["buckets"]["90+"] == "300.00"
    assert -Decimal(aging["total_open"]) == await h.account_balance("ap"), "aging != AP control"


async def test_payroll_run_read_model(harness: Harness) -> None:
    h = harness
    run = await ph.posted_run(h)
    summary = await h.call("GET", f"/api/v4a/payroll/runs/{run.run_id}")
    assert summary["status"] == "posted" and summary["workers"] == 1
    assert Decimal(summary["totals"]["gross"]) == ph.EXPECTED["gross"]
    assert Decimal(summary["totals"]["net"]) == ph.EXPECTED["net"]
    assert {x["type"] for x in summary["liabilities"]} == {
        "net_pay",
        "employee_tax",
        "employer_tax",
    }
    assert summary["posted_journal_id"]
    returns = await h.call("GET", "/api/v4b/returns")
    assert returns == []

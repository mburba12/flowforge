"""AP release workflow: vendor -> PO -> approve -> receive -> invoice -> match -> post -> pay."""

from decimal import Decimal

from .conftest import IN_PERIOD, Harness


async def _vendor(h: Harness) -> str:
    party = await h.organization("Acme Supplies LLC")
    vendor = await h.post(
        "/api/v3/vendors",
        json={"party_id": party, "default_currency": "USD", "ap_account_id": h.accounts["ap"]},
    )
    return str(vendor["id"])


async def _approved_po(h: Harness, vendor_id: str) -> tuple[str, list[str]]:
    po = await h.post(
        "/api/v3/purchase-orders",
        json={
            "vendor_id": vendor_id,
            "currency_code": "USD",
            "order_date": IN_PERIOD.isoformat(),
            "lines": [
                {
                    "description": "Widgets",
                    "quantity": "10",
                    "unit_price": "25.00",
                    "expense_account_id": h.accounts["expense"],
                },
                {
                    "description": "Fasteners",
                    "quantity": "4",
                    "unit_price": "12.50",
                    "expense_account_id": h.accounts["expense"],
                },
            ],
        },
    )
    assert po["status"] == "draft"
    po_id = po["id"]
    await h.post(f"/api/v3/purchase-orders/{po_id}/submit")
    await h.post(f"/api/v3/purchase-orders/{po_id}/approve", as_approver=True)
    rows = await h.sql(
        "SELECT id FROM purchase_order_lines WHERE purchase_order_id = :p ORDER BY line_number",
        p=po_id,
    )
    return po_id, [str(r[0]) for r in rows]


async def _invoice(
    h: Harness, vendor_id: str, po_id: str, lines: list[str], number: str, price: str = "25.00"
) -> str:
    invoice = await h.post(
        "/api/v3/vendor-invoices",
        json={
            "vendor_id": vendor_id,
            "purchase_order_id": po_id,
            "invoice_number": number,
            "invoice_date": IN_PERIOD.isoformat(),
            "due_date": "2026-02-14",
            "currency_code": "USD",
            "lines": [
                {
                    "po_line_id": lines[0],
                    "description": "Widgets",
                    "quantity": "10",
                    "unit_price": price,
                    "account_id": h.accounts["expense"],
                },
                {
                    "po_line_id": lines[1],
                    "description": "Fasteners",
                    "quantity": "4",
                    "unit_price": "12.50",
                    "account_id": h.accounts["expense"],
                },
            ],
        },
    )
    return str(invoice["id"])


def _post_params(h: Harness) -> dict[str, str]:
    return {"ledger_id": h.ledger_id, "period_id": h.period_id, "ap_account_id": h.accounts["ap"]}


def _pay_params(h: Harness, amount: str) -> dict[str, str]:
    return {
        "amount": amount,
        "payment_date": IN_PERIOD.isoformat(),
        "ledger_id": h.ledger_id,
        "period_id": h.period_id,
        "ap_account_id": h.accounts["ap"],
        "cash_account_id": h.accounts["cash"],
        "currency_code": "USD",
    }


async def test_ap_procure_to_pay(harness: Harness) -> None:
    h = harness
    audit_before = await h.audit_count()
    vendor_id = await _vendor(h)

    # Purchase order lifecycle and segregation of duties.
    po = await h.post(
        "/api/v3/purchase-orders",
        json={
            "vendor_id": vendor_id,
            "currency_code": "USD",
            "order_date": IN_PERIOD.isoformat(),
            "lines": [
                {
                    "description": "Widgets",
                    "quantity": "10",
                    "unit_price": "25.00",
                    "expense_account_id": h.accounts["expense"],
                },
                {
                    "description": "Fasteners",
                    "quantity": "4",
                    "unit_price": "12.50",
                    "expense_account_id": h.accounts["expense"],
                },
            ],
        },
    )
    po_id = po["id"]
    await h.post(f"/api/v3/purchase-orders/{po_id}/approve", as_approver=True, expect=409)
    await h.post(f"/api/v3/purchase-orders/{po_id}/submit")
    await h.require_two_people()
    await h.post(f"/api/v3/purchase-orders/{po_id}/approve", expect=409)  # creator
    approved = await h.post(f"/api/v3/purchase-orders/{po_id}/approve", as_approver=True)
    assert approved["status"] == "approved"
    lines = [
        str(r[0])
        for r in await h.sql(
            "SELECT id FROM purchase_order_lines WHERE purchase_order_id = :p ORDER BY line_number",
            p=po_id,
        )
    ]

    # Receiving: over-receipt rejected, full receipt accepted.
    await h.post(
        "/api/v3/goods-receipts",
        json={
            "purchase_order_id": po_id,
            "receipt_date": IN_PERIOD.isoformat(),
            "lines": [{"po_line_id": lines[0], "quantity": "11"}],
        },
        expect=409,
    )
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

    # Invoice, three-way match, posting (posting twice is rejected).
    invoice_id = await _invoice(h, vendor_id, po_id, lines, "INV-1001")
    match = await h.post(f"/api/v3/vendor-invoices/{invoice_id}/match")
    assert match["status"] == "matched", match
    posted = await h.post(f"/api/v3/vendor-invoices/{invoice_id}/post", params=_post_params(h))
    assert posted["status"] == "posted"
    await h.post(f"/api/v3/vendor-invoices/{invoice_id}/post", params=_post_params(h), expect=409)

    open_items = await h.sql(
        "SELECT id, original_amount, open_amount, status FROM ap_open_items WHERE invoice_id = :i",
        i=invoice_id,
    )
    assert len(open_items) == 1
    open_item_id, original, open_amount, status = open_items[0]
    assert (Decimal(original), Decimal(open_amount), status) == (
        Decimal("300.00"),
        Decimal("300.00"),
        "open",
    )
    await h.assert_ledger_integrity()
    assert await h.account_balance("ap") == Decimal("-300.00"), "AP control account != -300"
    assert await h.account_balance("expense") == Decimal("300.00")

    # Payments: invalid amounts rejected, partial then final payment, then closed.
    await h.post(
        f"/api/v3/ap/open-items/{open_item_id}/pay", params=_pay_params(h, "0"), expect=409
    )
    await h.post(
        f"/api/v3/ap/open-items/{open_item_id}/pay", params=_pay_params(h, "300.01"), expect=409
    )
    await h.post(f"/api/v3/ap/open-items/{open_item_id}/pay", params=_pay_params(h, "100.00"))
    await h.post(f"/api/v3/ap/open-items/{open_item_id}/pay", params=_pay_params(h, "200.00"))
    await h.post(
        f"/api/v3/ap/open-items/{open_item_id}/pay", params=_pay_params(h, "0.01"), expect=409
    )
    status_after = await h.sql(
        "SELECT open_amount, status FROM ap_open_items WHERE id = :i", i=open_item_id
    )
    assert (Decimal(status_after[0][0]), status_after[0][1]) == (Decimal("0.00"), "paid")

    await h.assert_ledger_integrity()
    assert await h.account_balance("ap") == Decimal("0.00")
    assert await h.account_balance("cash") == Decimal("-300.00")

    recon = await h.post(
        "/api/v3/ap/reconcile",
        params={
            "ledger_id": h.ledger_id,
            "period_id": h.period_id,
            "ap_account_id": h.accounts["ap"],
        },
    )
    assert recon["status"] == "reconciled", recon
    assert Decimal(recon["subledger_total"]) == Decimal(recon["gl_total"]) == Decimal("0")

    assert await h.audit_count() >= audit_before + 3, "PO, receipt and invoice must be audited"


async def test_ap_price_variance_blocks_posting(harness: Harness) -> None:
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
    invoice_id = await _invoice(h, vendor_id, po_id, lines, "INV-PV", price="27.00")
    match = await h.post(f"/api/v3/vendor-invoices/{invoice_id}/match")
    assert match["status"] == "exception"
    assert "price_variance" in match["details"]
    await h.post(f"/api/v3/vendor-invoices/{invoice_id}/post", params=_post_params(h), expect=409)
    assert await h.sql("SELECT 1 FROM ap_open_items WHERE invoice_id = :i", i=invoice_id) == []


async def test_ap_posting_rejected_in_closed_period(harness: Harness) -> None:
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
    invoice_id = await _invoice(h, vendor_id, po_id, lines, "INV-CLOSED")
    await h.post(f"/api/v3/vendor-invoices/{invoice_id}/match")
    await h.close_period()
    await h.post(f"/api/v3/vendor-invoices/{invoice_id}/post", params=_post_params(h), expect=409)
    assert await h.sql("SELECT 1 FROM ap_open_items WHERE invoice_id = :i", i=invoice_id) == []
    assert await h.sql("SELECT 1 FROM journal_entries") == [], "no journal may be written"

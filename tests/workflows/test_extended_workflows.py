"""Extended-domain workflows end to end (state machines that a single call cannot reach).

Each test drives one business process through the API as a user would, including the
second-person approval where the rules require it.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .conftest import IN_PERIOD, Harness
from .payroll_helpers import worker
from .test_ar_order_to_cash import _customer, _stocked_product


def key() -> str:
    return uuid4().hex


async def test_requisition_is_approved_and_converted_to_a_purchase_order(harness: Harness) -> None:
    h = harness
    product_id, _, _ = await _stocked_product(h)
    vendor_party = await h.organization("Parts Supplier")
    vendor = await h.post(
        "/api/v3/vendors",
        json={
            "party_id": vendor_party,
            "default_currency": "USD",
            "ap_account_id": h.accounts["ap"],
        },
    )
    req = await h.post(
        "/api/v2/commerce/final/requisitions",
        json={
            "number": f"REQ-{key()[:6]}",
            "lines": [
                {
                    "product_id": product_id,
                    "description": "Gadgets",
                    "quantity": "4",
                    "unit_price": "6.00",
                }
            ],
        },
    )
    action = f"/api/v2/commerce/final/requisitions/{req['id']}/action"
    await h.post(action, json={"target": "submitted", "idempotency_key": key()})
    await h.post(action, json={"target": "approved", "idempotency_key": key()}, as_approver=True)
    po = await h.post(
        f"/api/v2/commerce/completion/requisitions/{req['id']}/convert-po",
        json={
            "idempotency_key": key(),
            "vendor_id": vendor["id"],
            "currency_code": "USD",
            "expense_account_id": h.accounts["expense"],
        },
    )
    assert po, "conversion returns the purchase order"
    rows = await h.sql("SELECT count(*) FROM purchase_orders WHERE tenant_id = :t", t=h.tenant_id)
    assert rows[0][0] >= 1


async def test_transfer_between_warehouses(harness: Harness) -> None:
    h = harness
    product_id, source, _ = await _stocked_product(h)
    target = await h.post("/api/v3b/warehouses", json={"code": "WEST", "name": "West"})
    transfer = await h.post(
        "/api/v2/commerce/final/transfers",
        json={
            "number": f"TR-{key()[:6]}",
            "product_id": product_id,
            "source_warehouse_id": source,
            "target_warehouse_id": target["id"],
            "quantity": "5",
        },
    )
    await h.post("/api/v3b/locations", json={"warehouse_id": target["id"], "code": "W-01"})
    action = f"/api/v2/commerce/final/transfers/{transfer['id']}/action"
    # Completing needs approval first.
    await h.post(action, json={"target": "completed", "idempotency_key": key()}, expect=409)
    await h.post(action, json={"target": "approved", "idempotency_key": key()}, as_approver=True)
    await h.post(action, json={"target": "completed", "idempotency_key": key()})
    stock = dict(
        await h.sql(
            "SELECT warehouse_id::text, sum(on_hand) FROM inventory_balances"
            " WHERE product_id = :p GROUP BY warehouse_id",
            p=product_id,
        )
    )
    assert stock[source] == 45 and stock[target["id"]] == 5


async def test_quote_is_accepted_and_converted_to_a_sales_order(harness: Harness) -> None:
    h = harness
    product_id, _, _ = await _stocked_product(h)
    customer_id = await _customer(h, "Quote Customer", "10000")
    party = (await h.sql("SELECT party_id FROM customer_profiles WHERE id = :c", c=customer_id))[0][
        0
    ]
    quote = await h.post(
        "/api/v2/crm/quotes",
        json={
            "quote_number": f"Q-{key()[:6]}",
            "party_id": str(party),
            "currency_code": "USD",
            "lines": [
                {
                    "product_id": product_id,
                    "description": "Gadgets",
                    "quantity": "2",
                    "unit_price": "10.00",
                }
            ],
        },
    )
    transition = f"/api/v2/crm/quotes/{quote['id']}/transition"
    await h.post(transition, json={"target": "submitted"})
    await h.post(transition, json={"target": "approved"}, as_approver=True)
    await h.post(transition, json={"target": "accepted"}, as_approver=True)
    order = await h.post(
        f"/api/v2/crm/final/quotes/{quote['id']}/convert-order",
        json={
            "customer_id": customer_id,
            "ledger_id": h.ledger_id,
            "period_id": h.period_id,
            "order_date": IN_PERIOD.isoformat(),
        },
    )
    order_id = order.get("order_id") or order.get("id")
    total, status = (
        await h.sql("SELECT total_amount, status FROM sales_orders WHERE id = :o", o=order_id)
    )[0]
    assert total == 20 and status == "approved"  # numbered, credit-checked release order
    history = await h.sql(
        "SELECT count(*) FROM sales_order_status_events WHERE order_id = :o", o=order_id
    )
    assert history[0][0] >= 1


async def test_accrual_and_allocation_post_balanced_journals(harness: Harness) -> None:
    h = harness
    accrual = await h.post(
        "/api/v2/finance/completion/accruals",
        json={
            "code": f"ACC-{key()[:4]}",
            "ledger_id": h.ledger_id,
            "debit_account_id": h.accounts["expense"],
            "credit_account_id": h.accounts["ap"],
            "amount": "75.00",
        },
    )
    await h.post(
        f"/api/v2/finance/final/accruals/{accrual['id']}/post",
        json={
            "idempotency_key": key(),
            "journal_date": IN_PERIOD.isoformat(),
            "period_id": h.period_id,
        },
    )
    await h.post(
        "/api/v2/finance/final/allocations/post",
        json={
            "idempotency_key": key(),
            "journal_date": IN_PERIOD.isoformat(),
            "period_id": h.period_id,
            "source_account_id": h.accounts["expense"],
            "amount": "100.00",
            "targets": [
                {"account_id": h.accounts["cogs"], "basis_points": 6000},
                {"account_id": h.accounts["wages"], "basis_points": 4000},
            ],
        },
    )
    assert not await h.unbalanced_journals()


async def test_reconciliation_items_match_unmatch_and_certify(harness: Harness) -> None:
    h = harness
    session = await h.post(
        "/api/v2/finance/advanced/reconciliations",
        json={
            "account_id": h.accounts["cash"],
            "source_name": "Bank statement",
            "target_name": "Ledger",
            "source_balance": "100.00",
            "target_balance": "100.00",
        },
    )
    items = f"/api/v2/finance/completion/reconciliations/{session['id']}/items"
    a = await h.post(items, json={"source_reference": "STMT-1", "amount": "60.00"})
    b = await h.post(items, json={"source_reference": "STMT-2", "amount": "40.00"})
    ids = [a["id"], b["id"]]
    base = f"/api/v2/finance/final/reconciliations/{session['id']}"
    await h.post(f"{base}/match", json={"item_ids": ids, "target_reference": "GL-100"})
    await h.post(f"{base}/unmatch", json={"item_ids": ids, "target_reference": "GL-100"})
    await h.post(f"{base}/match", json={"item_ids": ids, "target_reference": "GL-100"})
    await h.post(
        f"/api/v2/finance/completion/reconciliations/{session['id']}/certify",
        json={"idempotency_key": key()},
        as_approver=True,
    )


async def test_payroll_adjustment_is_submitted_and_approved(harness: Harness) -> None:
    h = harness
    worker_id = await worker(h)
    adj = await h.post(
        "/api/v2/payroll-tax/final/adjustments",
        json={
            "worker_id": worker_id,
            "adjustment_type": "bonus",
            "amount": "50.00",
            "reason": "Spot bonus",
        },
    )
    action = f"/api/v2/payroll-tax/final/adjustments/{adj['id']}/action"
    await h.post(action, json={"target": "submitted", "idempotency_key": key()})
    await h.post(action, json={"target": "approved", "idempotency_key": key()}, as_approver=True)


async def test_entities_relate_match_and_merge(harness: Harness) -> None:
    h = harness
    a = await h.post(
        "/api/v4/entities", json={"entity_type": "organization", "display_name": "Acme Inc"}
    )
    b = await h.post(
        "/api/v4/entities",
        json={"entity_type": "organization", "display_name": "ACME Incorporated"},
    )
    await h.post(
        "/api/v4/entities/relationships",
        json={
            "source_entity_id": a["id"],
            "target_entity_id": b["id"],
            "relationship_type": "affiliate",
        },
    )
    proposal = await h.post(
        "/api/v4/entities/merge-proposals",
        json={
            "target_entity_id": a["id"],
            "member_entity_ids": [a["id"], b["id"]],
            "idempotency_key": key(),
        },
    )
    await h.post(f"/api/v4/entities/merge-proposals/{proposal['id']}/approve", as_approver=True)


async def test_subscription_lifecycle_and_entitlements(harness: Harness) -> None:
    h = harness
    customer = await h.organization("Subscriber Ltd")
    plan = await h.post(
        "/api/v2/bg08/final/plans",
        json={
            "code": f"PRO-{key()[:4]}",
            "name": "Pro",
            "billing_interval": "monthly",
            "price": "49.00",
            "currency_code": "USD",
        },
    )
    sub = await h.post(
        "/api/v2/bg08/final/subscriptions",
        json={
            "customer_id": customer,
            "plan_id": plan["id"],
            "starts_on": IN_PERIOD.isoformat(),
            "quantity": "1",
        },
    )
    await h.post(
        f"/api/v2/bg08/final/subscriptions/{sub['id']}/entitlements",
        json={"code": "seats", "limit_value": "5"},
    )
    await h.post(
        f"/api/v2/bg08/completion/subscriptions/{sub['id']}/entitlements/seats/consume",
        params={"quantity": "2"},
    )
    await h.post(f"/api/v2/bg08/final/subscriptions/{sub['id']}/action", json={"target": "paused"})
    await h.post(f"/api/v2/bg08/final/subscriptions/{sub['id']}/action", json={"target": "active"})


async def test_support_grant_is_issued_and_revoked(harness: Harness) -> None:
    h = harness
    owner = (await h.call("GET", "/api/v1/me"))["user_id"]
    approver = (await h.call("GET", "/api/v1/me", as_approver=True))["user_id"]
    grant = await h.post(
        "/api/v2/foundation-completion/support-grants",
        json={
            "support_user_id": approver,
            "scope": {"modules": ["finance"]},
            "reason": "Investigate a ledger question",
            "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "approved_by": owner,
        },
    )
    await h.post(
        f"/api/v2/foundation-final/support-grants/{grant['id']}/revoke",
        json={"decision": "revoke", "reason": "Done"},
    )

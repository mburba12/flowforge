"""More extended-domain workflows: every operation the earlier suites never completed.

Payments and treasury, assets, governance, CRM portal and campaigns, shipping,
recruiting, leave and lifecycle, reporting, uploads, entity matching, provider
connections (sandbox) and their signed webhooks.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .conftest import IN_PERIOD, Harness
from .payroll_helpers import worker
from .test_ar_order_to_cash import _customer, _order, _stocked_product

SANDBOX_SIGNATURE = "sandbox-valid-signature"


def key() -> str:
    return uuid4().hex


def iso(days: float = 0) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


async def test_payment_batch_is_approved_released_applied_and_reversed(harness: Harness) -> None:
    h = harness
    batch = await h.post(
        "/api/v2/finance/advanced/payment-batches",
        json={
            "batch_number": f"PB-{key()[:6]}",
            "kind": "ap",
            "currency_code": "USD",
            "total_amount": "300.00",
            "item_count": 2,
        },
    )
    items = f"/api/v2/finance/completion/payment-batches/{batch['id']}/items"
    await h.post(
        items, json={"source_type": "vendor_invoice", "source_id": str(uuid4()), "amount": "100.00"}
    )
    base = f"/api/v2/finance/completion/payment-batches/{batch['id']}"
    await h.post(f"{base}/release", json={"idempotency_key": key()}, expect=409)  # totals differ
    await h.post(
        items, json={"source_type": "vendor_invoice", "source_id": str(uuid4()), "amount": "200.00"}
    )
    await h.post(f"{base}/release", json={"idempotency_key": key()}, expect=409)  # not approved
    await h.post(f"{base}/approve", json={"idempotency_key": key()}, as_approver=True)
    await h.post(f"{base}/release", json={"idempotency_key": key()})
    gl = {
        "period_id": h.period_id,
        "journal_date": IN_PERIOD.isoformat(),
        "cash_account_id": h.accounts["cash"],
        "offset_account_id": h.accounts["ap"],
    }
    final = f"/api/v2/finance/final/payment-batches/{batch['id']}"
    await h.post(f"{final}/apply", json={"idempotency_key": key(), **gl})
    await h.post(f"{final}/reverse", json={"idempotency_key": key(), **gl})
    assert not await h.unbalanced_journals()


async def test_fixed_asset_and_asset_book_depreciate(harness: Harness) -> None:
    h = harness
    asset = await h.post(
        "/api/v2/finance/advanced/assets",
        json={
            "asset_number": f"FA-{key()[:6]}",
            "name": "Delivery van",
            "acquisition_date": IN_PERIOD.isoformat(),
            "cost": "1200.00",
            "useful_life_periods": 12,
        },
    )
    await h.post(f"/api/v2/finance/advanced/assets/{asset['id']}/depreciate")
    book = await h.post(
        "/api/v2/bg08/final/asset-books",
        json={
            "asset_id": asset["id"],
            "book_code": "TAX",
            "method": "straight_line",
            "useful_life_periods": 12,
        },
    )
    await h.post(f"/api/v2/bg08/final/asset-books/{book['id']}/depreciate")


async def test_governance_delegation_stewardship_quality_and_hierarchy(harness: Harness) -> None:
    h = harness
    owner = (await h.call("GET", "/api/v1/me"))["user_id"]
    approver = (await h.call("GET", "/api/v1/me", as_approver=True))["user_id"]
    delegation = {
        "grantor_id": owner,
        "delegate_id": approver,
        "scope": {"approve": ["journals"]},
        "starts_at": iso(),
        "expires_at": iso(7),
    }
    await h.post("/api/v2/foundation-final/delegations", json=delegation)
    await h.post(
        "/api/v2/foundation-final/delegations",
        json={**delegation, "delegate_id": owner},
        expect=422,
    )

    party = await h.organization("Stewarded Org")
    task = await h.post(
        "/api/v2/foundation-completion/stewardship",
        json={"party_id": party, "task_type": "review_duplicate"},
    )
    await h.post(
        f"/api/v2/foundation-final/stewardship/{task['id']}/decide",
        json={"decision": "approve", "reason": "Verified"},
    )

    rule = await h.post(
        "/api/v2/foundation-completion/quality-rules",
        json={
            "code": f"DQ-{key()[:4]}",
            "entity_type": "party",
            "rule_type": "required",
            "configuration": {"field": "tax_id"},
        },
    )
    passed = await h.post(
        f"/api/v2/foundation-final/quality-rules/{rule['id']}/run",
        json={"entity_id": party, "passed": True},
    )
    assert passed["issue_id"] is None
    failed = await h.post(
        f"/api/v2/foundation-final/quality-rules/{rule['id']}/run",
        json={"entity_id": party, "passed": False, "details": {"missing": "tax_id"}},
    )
    await h.post(
        f"/api/v2/foundation-final/quality-issues/{failed['issue_id']}/resolve",
        json={"decision": "remediate", "reason": "Tax id added"},
    )

    parent = await h.post(
        "/api/v2/organization-units",
        json={"unit_type": "department", "code": f"OPS-{key()[:4]}", "name": "Operations"},
    )
    child = await h.post(
        "/api/v2/organization-units",
        json={"unit_type": "team", "code": f"WH-{key()[:4]}", "name": "Warehouse"},
    )
    await h.post(f"/api/v2/foundation-final/organization-units/{child['id']}/parent/{parent['id']}")
    await h.post(
        f"/api/v2/foundation-final/organization-units/{parent['id']}/parent/{parent['id']}",
        expect=409,
    )


async def test_customer_portal_token_and_campaign_members(harness: Harness) -> None:
    h = harness
    party = await h.organization("Portal Customer")
    issued = await h.post(
        "/api/v2/crm/final/portal/tokens", json={"party_id": party, "expires_in_minutes": 30}
    )
    valid = await h.client.get(
        "/api/v2/crm/final/portal/validate", headers={**h.owner, "x-portal-token": issued["token"]}
    )
    assert valid.status_code == 200, valid.text
    bad = await h.client.get(
        "/api/v2/crm/final/portal/validate", headers={**h.owner, "x-portal-token": "nope"}
    )
    assert bad.status_code in (401, 403)

    campaign = await h.post(
        "/api/v2/crm/campaigns", json={"code": f"C-{key()[:4]}", "name": "Spring launch"}
    )
    lead = await h.post(
        "/api/v2/crm/leads", json={"lead_number": f"L-{key()[:6]}", "contact_name": "Jo Buyer"}
    )
    members = f"/api/v2/crm/completion/campaigns/{campaign['id']}/members"
    await h.post(members, json={"lead_id": lead["id"]})
    await h.post(members, json={"lead_id": lead["id"], "party_id": party}, expect=422)


async def test_shipment_labels_tracking_and_claims(harness: Harness) -> None:
    h = harness
    customer_id = await _customer(h, "Shipping Customer", "10000")
    product_id, _, _ = await _stocked_product(h)
    order = await _order(h, customer_id, product_id, "2")
    await h.post(f"/api/v3b/orders/{order['id']}/reserve")
    await h.post(
        f"/api/v3b/orders/{order['id']}/ship-invoice",
        params={"ship_date": IN_PERIOD.isoformat(), "due_date": IN_PERIOD.isoformat()},
    )
    shipment = str(
        (await h.sql("SELECT id FROM shipments WHERE order_id = :o", o=order["id"]))[0][0]
    )
    await h.post(
        "/api/v2/commerce/final/shipping/labels",
        json={
            "shipment_id": shipment,
            "carrier_code": "ups",
            "service_code": "ground",
            "idempotency_key": key(),
        },
    )
    await h.post(
        "/api/v2/commerce/final/shipping/tracking-events",
        json={
            "shipment_id": shipment,
            "event_code": "delivered",
            "description": "Left at door",
            "occurred_at": iso(),
        },
    )
    claim = await h.post(
        "/api/v2/commerce/final/shipping/claims",
        json={
            "shipment_id": shipment,
            "claim_number": f"CL-{key()[:6]}",
            "reason": "Damaged",
            "amount": "10.00",
        },
    )
    action = f"/api/v2/commerce/completion/claims/{claim['id']}/action"
    await h.post(action, json={"target": "submitted"})
    await h.post(action, json={"target": "approved"}, as_approver=True)
    await h.post(action, json={"target": "paid"}, as_approver=True)


async def test_recruiting_leave_lifecycle_and_reports(harness: Harness) -> None:
    h = harness
    position = await h.post(
        "/api/v2/workforce/final/positions",
        json={"code": f"P-{key()[:4]}", "title": "Picker", "headcount": 2},
    )
    candidate = await h.post(
        "/api/v2/workforce/final/candidates",
        json={
            "candidate_number": f"CAN-{key()[:6]}",
            "name": "Sam Applicant",
            "email": f"sam-{key()[:6]}@example.com",
            "consent": True,
        },
    )
    application = await h.post(
        "/api/v2/workforce/final/applications",
        json={"position_id": position["id"], "candidate_id": candidate["id"]},
    )
    transition = f"/api/v2/workforce/final/applications/{application['id']}/transition"
    await h.post(transition, json={"target": "hired"}, expect=409)  # stages cannot be skipped
    for stage in ("screening", "interview", "offer", "hired"):
        await h.post(transition, json={"target": stage})

    worker_id = await worker(h)
    policy = await h.post(
        "/api/v2/workforce/completion/leave-policies",
        json={"code": f"PTO-{key()[:4]}", "name": "Paid time off", "annual_entitlement": "20"},
    )
    start = IN_PERIOD
    leave = await h.post(
        "/api/v2/workforce/completion/leave",
        json={
            "worker_id": worker_id,
            "policy_id": policy["id"],
            "starts_on": start.isoformat(),
            "ends_on": (start + timedelta(days=1)).isoformat(),
            "units": "2",
        },
    )
    action = f"/api/v2/workforce/completion/leave/{leave['id']}/action"
    await h.post(action, json={"target": "submitted", "idempotency_key": key()})
    await h.post(action, json={"target": "approved", "idempotency_key": key()}, as_approver=True)

    task = await h.post(
        "/api/v2/workforce/completion/lifecycle-tasks",
        json={
            "worker_id": worker_id,
            "lifecycle_type": "onboarding",
            "task_code": "LAPTOP",
            "title": "Issue laptop",
        },
    )
    task_action = f"/api/v2/workforce/completion/lifecycle-tasks/{task['id']}/action"
    await h.post(task_action, json={"target": "in_progress", "idempotency_key": key()})
    await h.post(task_action, json={"target": "completed", "idempotency_key": key()})

    for code in ("recruiting_funnel", "leave"):
        await h.post("/api/v2/workforce/ultimate/reports", json={"report_code": code})
    await h.post("/api/v2/workforce/ultimate/reports", json={"report_code": "nope"}, expect=422)


async def test_upload_inspection_entity_matching_and_lookups(harness: Harness) -> None:
    h = harness
    await h.post("/api/v4/ai/uploads/inspect", json={"filename": "invoice.pdf", "size_bytes": 2048})
    await h.post(
        "/api/v4/ai/uploads/inspect", json={"filename": "run.exe", "size_bytes": 2048}, expect=422
    )

    refs = []
    for name in ("Acme Inc", "ACME Incorporated"):
        entity = await h.post(
            "/api/v4/entities", json={"entity_type": "organization", "display_name": name}
        )
        ref = await h.post(
            f"/api/v4/entities/{entity['id']}/lineage",
            json={
                "source_system": "crm",
                "source_table": "accounts",
                "source_record_id": key(),
                "identity_fingerprint": hashlib.sha256(name.encode()).hexdigest(),
                "link_method": "manual",
                "link_confidence": 100,
            },
        )
        refs.append(ref["id"])
    await h.post(
        "/api/v4/entities/match",
        json={
            "left_reference_id": refs[0],
            "right_reference_id": refs[1],
            "signals": {"tax_identifier_hash_exact": True},
        },
    )

    capabilities = await h.call("GET", "/api/v1/control-plane/capabilities")
    items = (
        capabilities
        if isinstance(capabilities, list)
        else capabilities.get("items", capabilities.get("capabilities", []))
    )
    code = items[0]["code"] if isinstance(items[0], dict) else items[0]
    await h.call("GET", f"/api/v1/control-plane/capabilities/{code}")

    party = await h.organization("Lookup Org")
    record = await h.call("GET", f"/api/v1/business/parties/{party}")
    assert record


async def test_sandbox_provider_connections_sync_and_signed_webhooks(harness: Harness) -> None:
    h = harness
    event = {
        "provider_event_id": key(),
        "event_type": "updated",
        "payload": json.dumps({"id": "evt"}),
    }
    payments = await h.post(
        "/api/v4c/payments/connections",
        json={"provider": "stripe_sandbox", "authorization_code": "sandbox-auth"},
    )
    await h.post(
        f"/api/v4c/payments/connections/{payments['id']}/sync", json={"include_payouts": True}
    )
    webhook = f"/api/v4c/payments/connections/{payments['id']}/webhooks"
    await h.post(webhook, json={**event, "signature": "forged"}, expect=(401, 409))
    await h.post(webhook, json={**event, "signature": SANDBOX_SIGNATURE}, expect=202)

    for domain in ("commerce", "logistics", "finance", "workforce", "engagement"):
        providers = await h.call("GET", f"/api/v4c/{domain}/providers")
        listing = (
            providers
            if isinstance(providers, list)
            else providers.get("items", providers.get("providers", []))
        )
        provider = listing[0] if isinstance(listing[0], str) else listing[0]["code"]
        connection = await h.post(
            f"/api/v4c/{domain}/connections",
            json={"provider": provider, "authorization_code": "sandbox-auth"},
        )
        await h.post(
            f"/api/v4c/{domain}/connections/{connection['id']}/webhooks",
            json={**event, "provider_event_id": key(), "signature": SANDBOX_SIGNATURE},
            expect=202,
        )

    await h.post("/api/v4c/connections/link-session", json={})
    bank = await h.post(
        "/api/v4c/connections/exchange", json={"public_token": "sandbox-public-token"}
    )
    await h.post(f"/api/v4c/connections/{bank['id']}/sync")
    account = str(
        (
            await h.sql(
                "SELECT id FROM connected_bank_accounts WHERE connection_id = :c LIMIT 1",
                c=bank["id"],
            )
        )[0][0]
    )
    await h.call(
        "PUT",
        f"/api/v4c/accounts/{account}/gl-mapping",
        json={"gl_account_id": h.accounts["cash"], "mapping_type": "cash"},
    )
    await h.post(
        "/api/v4c/transactions/manual",
        json={
            "connected_bank_account_id": account,
            "provider_transaction_id": f"tx-{key()[:8]}",
            "posted_at": iso(),
            "amount": "12.50",
            "currency_code": "USD",
            "direction": "debit",
            "description": "Bank fee",
        },
    )

    provider = await h.post(
        "/api/v2/bg11/connections",
        json={"provider_type": "payment", "provider_code": "stripe", "mode": "sandbox"},
    )
    operation = {
        "connection_id": provider["id"],
        "operation": "refund",
        "idempotency_key": key(),
        "request": {"amount": "5.00"},
    }
    await h.post("/api/v2/bg11/operations", json=operation, expect=409)  # not certified yet
    status = f"/api/v2/bg11/connections/{provider['id']}/status"
    current = (
        await h.sql("SELECT status FROM bg11_provider_connections WHERE id = :i", i=provider["id"])
    )[0][0]
    if current != "configured":
        await h.post(status, json={"target": "configured"})
    await h.post(status, json={"target": "sandbox_certified"})
    await h.post("/api/v2/bg11/operations", json=operation)


async def test_only_platform_operators_create_tenants(harness: Harness) -> None:
    # Tenant creation is a platform-operator action; no tenant role grants it.
    await harness.post(
        "/api/v1/tenants", json={"name": "Other", "slug": f"other-{key()[:6]}"}, expect=403
    )

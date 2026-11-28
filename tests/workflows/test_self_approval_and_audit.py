"""Two-person approval exceptions, the full audit export and record pickers."""

import csv
import io

from .conftest import Harness
from .test_gl_journal_controls import _journal


async def test_owner_may_approve_own_journal(harness: Harness) -> None:
    h = harness
    journal = await h.post("/api/v2/journals", json=_journal(h, "10.00", "10.00"))
    approved = await h.post(f"/api/v2/journals/{journal['id']}/approve")
    assert approved["status"] == "approved"


async def test_designated_person_may_approve_own_work(harness: Harness) -> None:
    h = harness
    # The approver (a Manager) creates a journal: by default they cannot approve it.
    journal = await h.post("/api/v2/journals", json=_journal(h, "20.00", "20.00"), as_approver=True)
    await h.post(f"/api/v2/journals/{journal['id']}/approve", as_approver=True, expect=409)

    users = await h.call("GET", "/api/v1/users")
    approver = next(u for u in users if str(u["email"]).startswith("approver-"))
    roles = {r["name"]: r for r in await h.call("GET", "/api/v1/roles")}
    assert roles["Approve own work"]["permissions"] == ["approvals.self_approve"]
    assert "approvals.self_approve" in roles["Owner"]["permissions"]
    assert "approvals.self_approve" not in roles["Manager"]["permissions"]

    # The owner designates them; now they may approve their own journal.
    await h.post(f"/api/v1/users/{approver['id']}/roles", json={"role": "Approve own work"})
    approved = await h.post(f"/api/v2/journals/{journal['id']}/approve", as_approver=True)
    assert approved["status"] == "approved"

    # Removing the designation restores the two-person rule.
    await h.call("DELETE", f"/api/v1/users/{approver['id']}/roles/Approve%20own%20work")
    second = await h.post("/api/v2/journals", json=_journal(h, "5.00", "5.00"), as_approver=True)
    await h.post(f"/api/v2/journals/{second['id']}/approve", as_approver=True, expect=409)


async def test_audit_screen_shows_100_and_export_has_everything(harness: Harness) -> None:
    h = harness
    for index in range(110):
        await h.sql(
            "INSERT INTO audit_entries (id, tenant_id, action, resource_type, resource_id, payload,"
            " occurred_at)"
            " VALUES (gen_random_uuid(), :t, 'tested', 'audit_probe', :r, '{\"n\": 1}', now())",
            t=h.tenant_id,
            r=f"probe-{index}",
        )
    total = (await h.sql("SELECT count(*) FROM audit_entries"))[0][0]
    assert total > 100

    screen = await h.call("GET", "/api/v1/audit")
    assert len(screen) == 100
    assert {"occurred_at", "user", "action", "resource_type", "resource_id"} <= set(screen[0])

    response = await h.client.get("/api/v1/audit/export", headers=h.owner)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert rows[0] == ["occurred_at", "user", "action", "record_type", "record_id", "details"]
    assert len(rows) - 1 == total
    assert sum(1 for r in rows if r[3] == "audit_probe") == 110
    # The export itself is audited.
    exported = await h.sql("SELECT count(*) FROM audit_entries WHERE action = 'exported'")
    assert exported[0][0] == 1


async def test_audit_export_needs_audit_permission(harness: Harness) -> None:
    h = harness
    response = await h.client.get("/api/v1/audit/export")
    assert response.status_code == 401


async def test_more_tools_forms_offer_record_pickers(harness: Harness) -> None:
    h = harness
    catalog = await h.call("GET", "/api/v1/operations", params={"workspace": "finance-advanced"})
    refs: set[str] = set()
    for op in catalog["operations"]:
        refs |= {p["ref"] for p in op["parameters"] if p.get("ref")}
        body = op["body"] or {}
        for prop in (body.get("properties") or {}).values():
            if isinstance(prop, dict) and prop.get("x-ref"):
                refs.add(prop["x-ref"])
    assert {"accounts", "ledgers", "accounting_periods"} <= refs
    # Every referenced table can be listed for the drop-down.
    for table in sorted(refs):
        page = await h.call("GET", f"/api/v1/business/{table}", params={"limit": 1})
        assert "items" in page, table

"""Role-based access control for the release-scope API (allow and deny paths)."""

from uuid import uuid4

from flowforge.main import app
from flowforge.platform.authorization import (
    CATALOG,
    EXTENDED_POLICY,
    POLICY,
    PUBLIC,
    RELEASE_MODULES,
    STANDARD_ROLES,
    endpoint_key,
    iter_api_routes,
)

from .conftest import IN_PERIOD, Harness


def _endpoint_keys(modules: set[str] | None = None) -> set[str]:
    return {
        endpoint_key(route.endpoint)
        for route in iter_api_routes(list(app.routes))
        if modules is None or route.endpoint.__module__ in modules
    }


def test_every_release_endpoint_has_a_policy() -> None:
    endpoints = _endpoint_keys(RELEASE_MODULES)
    assert endpoints - set(POLICY) - PUBLIC == set(), "release endpoints without a policy"
    assert set(POLICY) - endpoints == set(), "policy entries for endpoints that do not exist"


def test_every_endpoint_is_public_or_has_a_policy() -> None:
    endpoints = _endpoint_keys()
    unmapped = endpoints - PUBLIC - set(POLICY) - set(EXTENDED_POLICY)
    assert not unmapped, sorted(unmapped)
    assert {code for code in EXTENDED_POLICY.values() if code} <= set(CATALOG)
    # Public endpoints are sign-in, health, problem reports and static diagnostics only.
    signin_steps = {
        "flowforge.accounts.routes:auth_config",
        "flowforge.accounts.routes:mfa_verify",
        "flowforge.accounts.routes:forgot_password",
        "flowforge.accounts.routes:reset_password",
        "flowforge.accounts.routes:verify_email",
    }
    for key in PUBLIC - signin_steps:
        module, name = key.split(":")
        assert module.endswith((".auth", ".health", "support_feedback")) or name in {
            "status",
            "health",
            "phase1_status",
        }, key


def test_policy_uses_known_permissions_and_roles_are_consistent() -> None:
    assert {code for code in POLICY.values() if code} <= set(CATALOG)
    for role, codes in STANDARD_ROLES.items():
        assert codes <= set(CATALOG), role
    assert "platform.tenants.create" not in set().union(*STANDARD_ROLES.values())
    assert STANDARD_ROLES["Viewer"] <= STANDARD_ROLES["Clerk"]
    assert not {"users.manage", "roles.manage"} & STANDARD_ROLES["Manager"]


async def _user(h: Harness, role: str | None) -> tuple[str, dict[str, str]]:
    slug = (await h.sql("SELECT slug FROM tenants WHERE id = :t", t=h.tenant_id))[0][0]
    email = f"{(role or 'none').lower()}-{uuid4().hex[:8]}@example.com"
    password = f"Rbac-{uuid4().hex}"
    made = await h.post(
        "/api/v1/users",
        json={
            "email": email,
            "display_name": f"{role} user",
            "password": password,
            "roles": [role] if role else [],
        },
    )
    login = await h.client.post(
        "/api/v1/auth/login", json={"email": email, "password": password, "tenant_slug": slug}
    )
    assert login.status_code == 200, login.text
    return str(made["id"]), {"Authorization": f"Bearer {login.json()['access_token']}"}


def _journal(h: Harness) -> dict[str, object]:
    return {
        "ledger_id": h.ledger_id,
        "period_id": h.period_id,
        "journal_date": IN_PERIOD.isoformat(),
        "description": "RBAC test",
        "lines": [
            {
                "account_id": h.accounts["cash"],
                "debit": "10.00",
                "credit": "0",
                "currency_code": "USD",
            },
            {
                "account_id": h.accounts["equity"],
                "debit": "0",
                "credit": "10.00",
                "currency_code": "USD",
            },
        ],
    }


async def _status(h: Harness, method: str, path: str, headers: dict[str, str], **kw: object) -> int:
    response = await h.client.request(method, path, headers=headers, **kw)  # type: ignore[arg-type]
    return response.status_code


async def test_owner_has_full_catalog_except_platform(harness: Harness) -> None:
    h = harness
    mine = await h.call("GET", "/api/v1/me/permissions")
    assert set(mine["permissions"]) == STANDARD_ROLES["Owner"]
    roles = {r["name"]: r for r in await h.call("GET", "/api/v1/roles")}
    assert set(STANDARD_ROLES) <= set(roles)


async def test_viewer_reads_but_cannot_write(harness: Harness) -> None:
    h = harness
    _, viewer = await _user(h, "Viewer")
    tb = {"ledger_id": h.ledger_id, "period_id": h.period_id}
    assert await _status(h, "GET", "/api/v2/trial-balance", viewer, params=tb) == 200
    assert await _status(h, "GET", "/api/v1/business/users", viewer) == 200
    assert await _status(h, "POST", "/api/v2/journals", viewer, json=_journal(h)) == 403
    assert await _status(h, "POST", "/api/v3/vendors", viewer, json={}) == 403
    assert await _status(h, "GET", "/api/v1/audit", viewer) == 403
    assert await _status(h, "GET", "/api/v1/users", viewer) == 403


async def test_clerk_creates_but_cannot_approve_or_post(harness: Harness) -> None:
    h = harness
    _, clerk = await _user(h, "Clerk")
    _, approver = await _user(h, "Approver")
    created = await h.client.post("/api/v2/journals", headers=clerk, json=_journal(h))
    assert created.status_code == 201, created.text
    journal_id = created.json()["id"]
    assert await _status(h, "POST", f"/api/v2/journals/{journal_id}/approve", clerk) == 403
    assert await _status(h, "POST", "/api/v2/journals", approver, json=_journal(h)) == 403
    assert await _status(h, "POST", f"/api/v2/journals/{journal_id}/approve", approver) == 200
    assert await _status(h, "POST", f"/api/v2/journals/{journal_id}/post", clerk) == 403
    assert await _status(h, "POST", f"/api/v2/journals/{journal_id}/post", approver) == 200


async def test_user_without_roles_is_denied_everything_but_identity(harness: Harness) -> None:
    h = harness
    _, nobody = await _user(h, None)
    assert await _status(h, "GET", "/api/v1/me", nobody) == 200
    assert await _status(h, "GET", "/api/v1/business/resources", nobody) == 403
    tb = {"ledger_id": h.ledger_id, "period_id": h.period_id}
    assert await _status(h, "GET", "/api/v2/trial-balance", nobody, params=tb) == 403


async def test_deactivated_user_loses_access_immediately(harness: Harness) -> None:
    h = harness
    user_id, viewer = await _user(h, "Viewer")
    assert await _status(h, "GET", "/api/v1/business/users", viewer) == 200
    await h.call("PATCH", f"/api/v1/users/{user_id}", json={"is_active": False})
    assert await _status(h, "GET", "/api/v1/business/users", viewer) == 401
    await h.call("PATCH", f"/api/v1/users/{user_id}", json={"is_active": True})
    assert await _status(h, "GET", "/api/v1/business/users", viewer) == 200


async def test_role_changes_take_effect_and_are_audited(harness: Harness) -> None:
    h = harness
    user_id, user = await _user(h, "Viewer")
    assert await _status(h, "POST", "/api/v2/journals", user, json=_journal(h)) == 403
    await h.post(f"/api/v1/users/{user_id}/roles", json={"role": "Clerk"})
    assert await _status(h, "POST", "/api/v2/journals", user, json=_journal(h)) == 201
    await h.call("DELETE", f"/api/v1/users/{user_id}/roles/Clerk")
    assert await _status(h, "POST", "/api/v2/journals", user, json=_journal(h)) == 403
    actions = {
        r[0]
        for r in await h.sql("SELECT action FROM audit_entries WHERE resource_id = :u", u=user_id)
    }
    assert {"created", "role_assigned", "role_removed"} <= actions


async def test_tenant_boundaries_and_admin_protections(harness: Harness) -> None:
    h = harness
    tenants = await h.call("GET", "/api/v1/tenants")
    assert [t["id"] for t in tenants] == [str(h.tenant_id)], "tenant list must be own tenant only"
    assert (
        await _status(
            h,
            "POST",
            "/api/v1/tenants",
            h.owner,
            json={"name": "Rogue", "slug": f"rogue-{uuid4().hex[:6]}"},
        )
        == 403
    )
    owner_role = next(r for r in await h.call("GET", "/api/v1/roles") if r["name"] == "Owner")
    await h.call(
        "PUT", f"/api/v1/roles/{owner_role['id']}/permissions", json={"permissions": []}, expect=409
    )
    me = await h.call("GET", "/api/v1/me")
    await h.call("PATCH", f"/api/v1/users/{me['user_id']}", json={"is_active": False}, expect=409)
    _, manager = await _user(h, "Manager")
    assert await _status(h, "POST", "/api/v1/users", manager, json={}) == 403
    assert await _status(h, "GET", "/api/v1/roles", manager) == 403


async def test_custom_role_permissions(harness: Harness) -> None:
    h = harness
    role = await h.post("/api/v1/roles", json={"name": "AP Reader"})
    await h.call(
        "PUT",
        f"/api/v1/roles/{role['id']}/permissions",
        json={"permissions": ["ap.read", "gl.read"]},
    )
    await h.call(
        "PUT",
        f"/api/v1/roles/{role['id']}/permissions",
        json={"permissions": ["no.such"]},
        expect=422,
    )
    user_id, user = await _user(h, None)
    await h.post(f"/api/v1/users/{user_id}/roles", json={"role": "AP Reader"})
    tb = {"ledger_id": h.ledger_id, "period_id": h.period_id}
    assert await _status(h, "GET", "/api/v2/trial-balance", user, params=tb) == 200
    assert await _status(h, "POST", "/api/v2/journals", user, json=_journal(h)) == 403


async def test_startup_sync_restores_standard_grants(harness: Harness) -> None:
    from flowforge.platform.authorization import sync_standard_roles

    h = harness
    await h.sql(
        "DELETE FROM role_permissions rp USING roles r, permissions p"
        " WHERE rp.role_id = r.id AND rp.permission_id = p.id AND r.name = 'Viewer'"
        " AND p.code = 'gl.read' AND r.tenant_id = :t",
        t=h.tenant_id,
    )
    added = await sync_standard_roles()
    assert added["grants"] >= 1
    viewer = next(r for r in await h.call("GET", "/api/v1/roles") if r["name"] == "Viewer")
    assert "gl.read" in viewer["permissions"]
    assert (await sync_standard_roles())["grants"] == 0


async def test_extended_domains_enforce_read_write_approve(harness: Harness) -> None:
    h = harness
    _, viewer = await _user(h, "Viewer")
    _, clerk = await _user(h, "Clerk")
    _, approver = await _user(h, "Approver")
    _, nobody = await _user(h, None)
    leads = "/api/v2/crm/final/leads"
    # read: any standard role with domain read; no role -> forbidden; no token -> 401
    assert await _status(h, "GET", leads, viewer) == 200
    assert await _status(h, "GET", leads, nobody) == 403
    assert (await h.client.get(leads)).status_code == 401
    # write: clerk passes authorization (body validation answers), viewer/approver do not
    assert await _status(h, "POST", "/api/v2/crm/leads", viewer, json={}) == 403
    assert await _status(h, "POST", "/api/v2/crm/leads", approver, json={}) == 403
    assert await _status(h, "POST", "/api/v2/crm/leads", clerk, json={}) == 422
    # approve-level path: clerk denied, approver authorized
    close = f"/api/v2/finance/completion/close-runs/{uuid4()}/close"
    assert await _status(h, "POST", close, clerk, json={}) == 403
    assert await _status(h, "POST", close, approver, json={}) != 403
    # generic transition: deciding (won) needs approve, progressing does not
    transition = f"/api/v2/crm/final/opportunities/{uuid4()}/transition"
    won = {"stage": "won", "probability": 100}
    progress = {"stage": "proposal", "probability": 40}
    assert await _status(h, "POST", transition, clerk, json=won) == 403
    assert await _status(h, "POST", transition, clerk, json=progress) != 403
    # governance stays with owners and managers
    assert await _status(h, "POST", "/api/v2/foundation-final/delegations", clerk, json={}) == 403
    assert await _status(h, "POST", "/api/v2/foundation-final/delegations", h.owner, json={}) == 422


async def test_public_endpoints_need_no_token(harness: Harness) -> None:
    h = harness
    assert (await h.client.get("/api/v1/health")).status_code == 200
    assert (await h.client.get("/phase4a/status")).status_code == 200

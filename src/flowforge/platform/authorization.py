"""Role-based access control for the release-scope API (platform, GL, AP, AR, payroll, tax).

* CATALOG: every permission code with its description (seeded by migration ff_rbac_001).
* STANDARD_ROLES: permission sets for the built-in roles created for every tenant.
* POLICY: the permission each release-scope endpoint requires, keyed by the endpoint
  function ("module:qualname") because nested include_router prefixes make route
  paths unreliable for matching.
* enforce(): app-wide dependency. For an endpoint in a release module it requires a
  valid token, an active user in an active tenant, and the mapped permission; an
  unmapped endpoint in a release module is denied (deny by default). Endpoints in
  other (extended) modules keep their own authentication unchanged.
"""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text

from flowforge.core.security import Principal, current_principal

CATALOG: dict[str, str] = {
    # platform
    "tenant.read": "View own tenant",
    "tenant.manage": "Manage tenant settings",
    "platform.tenants.create": "Create tenants (platform operators; no tenant role)",
    "users.manage": "Create, update, deactivate users and assign roles",
    "roles.manage": "Create roles and set role permissions",
    "audit.read": "Read the audit trail",
    "documents.manage": "Manage documents",
    "workflows.manage": "Manage workflow definitions",
    "integrations.manage": "Manage integration connections",
    "notifications.manage": "Create notifications",
    "business.read": "Browse business records (generic read-only browser)",
    # master data
    "masterdata.read": "Read parties and organization units",
    "masterdata.write": "Create parties and organization units",
    # general ledger
    "gl.read": "Read ledgers, periods and trial balance",
    "gl.setup": "Create currencies, calendars, ledgers and accounts",
    "gl.journal.write": "Create journals",
    "gl.journal.approve": "Approve journals",
    "gl.journal.post": "Post journals",
    "gl.period.manage": "Create, close and reopen accounting periods",
    # accounts payable
    "ap.read": "Read AP documents, open items and aging",
    "ap.vendor.write": "Create vendors",
    "ap.po.write": "Create and submit purchase orders",
    "ap.po.approve": "Approve purchase orders",
    "ap.receive": "Record goods receipts",
    "ap.invoice.write": "Create and match vendor invoices",
    "ap.invoice.post": "Post vendor invoices to the ledger",
    "ap.pay": "Pay AP open items",
    "ap.reconcile": "Run AP reconciliation",
    # accounts receivable, orders, inventory
    "ar.read": "Read customers, orders, invoices, open items and aging",
    "ar.customer.write": "Create customers",
    "ar.order.write": "Create sales orders",
    "ar.order.fulfill": "Reserve, ship and invoice sales orders",
    "ar.receipt.write": "Record customer receipts",
    "inventory.setup": "Create products, warehouses and locations",
    "inventory.write": "Adjust inventory",
    # workforce and payroll
    "workforce.read": "Read workers and workforce records",
    "workforce.write": "Maintain workers, compensation, profiles, schedules, time and leave",
    "workforce.approve": "Approve time entries",
    "payroll.read": "Read payroll runs and results",
    "payroll.setup": "Create pay groups and pay periods",
    "payroll.run.write": "Create and calculate payroll runs",
    "payroll.run.approve": "Approve payroll runs",
    "payroll.run.post": "Post payroll runs to the ledger",
    "payroll.pay": "Pay workers",
    "payroll.reconcile": "Reconcile payroll runs",
    # tax
    "tax.read": "Read tax configuration, liabilities and returns",
    "tax.setup": "Maintain jurisdictions, rules, authorities and worker elections",
    "tax.calculate": "Run tax calculations",
    "tax.liability.write": "Create tax liabilities",
    "tax.return.write": "Create tax returns",
    "tax.return.approve": "Approve tax returns",
    "tax.remit": "Remit tax payments",
    "tax.notice.manage": "Record and resolve tax notices",
    "tax.reconcile": "Reconcile tax accounts",
}

_READ = {c for c in CATALOG if c.endswith(".read")} - {"audit.read"}
_APPROVE = {
    "ap.po.approve",
    "gl.journal.approve",
    "gl.journal.post",
    "payroll.run.approve",
    "tax.return.approve",
    "workforce.approve",
}
_CLERK_WRITE = {
    "masterdata.write",
    "gl.journal.write",
    "ap.vendor.write",
    "ap.po.write",
    "ap.receive",
    "ap.invoice.write",
    "ar.customer.write",
    "ar.order.write",
    "ar.order.fulfill",
    "ar.receipt.write",
    "inventory.write",
    "workforce.write",
    "payroll.run.write",
    "tax.calculate",
    "tax.liability.write",
    "tax.return.write",
    "tax.notice.manage",
    "documents.manage",
    "notifications.manage",
}
_ADMIN_ONLY = {"users.manage", "roles.manage", "tenant.manage", "platform.tenants.create"}

STANDARD_ROLES: dict[str, set[str]] = {
    "Owner": set(CATALOG) - {"platform.tenants.create"},
    "Manager": set(CATALOG) - _ADMIN_ONLY,
    "Approver": _READ | _APPROVE,
    "Clerk": _READ | _CLERK_WRITE,
    "Viewer": set(_READ),
}

RELEASE_MODULES = {
    "flowforge.api.routes.platform",
    "flowforge.api.routes.tenants",
    "flowforge.api.routes.users",
    "flowforge.phase2a.routes",
    "flowforge.phase2b.routes",
    "flowforge.phase3a.routes",
    "flowforge.phase3a.integration_routes",
    "flowforge.phase3a.payment_routes",
    "flowforge.phase3b.routes",
    "flowforge.phase4a.routes",
    "flowforge.phase4a_stage2.routes",
    "flowforge.phase4a_stage3.routes",
    "flowforge.phase4b.routes",
    "flowforge.phase4b_stage2.routes",
    "flowforge.resource_contracts.router",
    "flowforge.release.read_routes",
    "flowforge.release.admin_routes",
}

AUTHENTICATED = ""  # mapped, but any active user of the tenant may call it

POLICY: dict[str, str] = {
    # platform
    "flowforge.api.routes.platform:me": AUTHENTICATED,
    "flowforge.api.routes.platform:audit": "audit.read",
    "flowforge.api.routes.platform:create_role": "roles.manage",
    "flowforge.api.routes.platform:document": "documents.manage",
    "flowforge.api.routes.platform:integration": "integrations.manage",
    "flowforge.api.routes.platform:notification": "notifications.manage",
    "flowforge.api.routes.platform:workflow": "workflows.manage",
    "flowforge.api.routes.tenants:create_tenant": "platform.tenants.create",
    "flowforge.api.routes.tenants:list_tenants": "tenant.read",
    "flowforge.resource_contracts.router:resources": "business.read",
    "flowforge.resource_contracts.router:list_records": "business.read",
    "flowforge.resource_contracts.router:get_record": "business.read",
    # users and roles
    "flowforge.api.routes.users:list_users": "users.manage",
    "flowforge.api.routes.users:create_user": "users.manage",
    "flowforge.api.routes.users:update_user": "users.manage",
    "flowforge.api.routes.users:assign_role": "users.manage",
    "flowforge.api.routes.users:remove_role": "users.manage",
    "flowforge.api.routes.users:list_roles": "roles.manage",
    "flowforge.api.routes.users:set_role_permissions": "roles.manage",
    "flowforge.api.routes.users:list_permissions": "roles.manage",
    "flowforge.api.routes.users:my_permissions": AUTHENTICATED,
    # master data
    "flowforge.phase2a.routes:create_organization": "masterdata.write",
    "flowforge.phase2a.routes:create_person": "masterdata.write",
    "flowforge.phase2a.routes:create_unit": "masterdata.write",
    "flowforge.phase2a.routes:get_party": "masterdata.read",
    "flowforge.phase2a.routes:search_parties": "masterdata.read",
    # general ledger
    "flowforge.phase2b.routes:create_currency": "gl.setup",
    "flowforge.phase2b.routes:create_calendar": "gl.setup",
    "flowforge.phase2b.routes:create_ledger": "gl.setup",
    "flowforge.phase2b.routes:create_account": "gl.setup",
    "flowforge.phase2b.routes:create_period": "gl.period.manage",
    "flowforge.phase2b.routes:create_journal": "gl.journal.write",
    "flowforge.phase2b.routes:approve_journal": "gl.journal.approve",
    "flowforge.phase2b.routes:post_journal": "gl.journal.post",
    "flowforge.phase2b.routes:trial_balance": "gl.read",
    # accounts payable
    "flowforge.phase3a.routes:vendor": "ap.vendor.write",
    "flowforge.phase3a.routes:purchase_order": "ap.po.write",
    "flowforge.phase3a.routes:submit": "ap.po.write",
    "flowforge.phase3a.routes:approve": "ap.po.approve",
    "flowforge.phase3a.routes:receipt": "ap.receive",
    "flowforge.phase3a.routes:invoice": "ap.invoice.write",
    "flowforge.phase3a.integration_routes:match_invoice": "ap.invoice.write",
    "flowforge.phase3a.integration_routes:post_invoice": "ap.invoice.post",
    "flowforge.phase3a.payment_routes:pay": "ap.pay",
    "flowforge.phase3a.payment_routes:reconcile": "ap.reconcile",
    # accounts receivable, orders, inventory
    "flowforge.phase3b.routes:create_customer": "ar.customer.write",
    "flowforge.phase3b.routes:create_product": "inventory.setup",
    "flowforge.phase3b.routes:create_warehouse": "inventory.setup",
    "flowforge.phase3b.routes:create_location": "inventory.setup",
    "flowforge.phase3b.routes:adjust_inventory": "inventory.write",
    "flowforge.phase3b.routes:create_order": "ar.order.write",
    "flowforge.phase3b.routes:reserve_order": "ar.order.fulfill",
    "flowforge.phase3b.routes:ship_and_invoice_order": "ar.order.fulfill",
    "flowforge.phase3b.routes:create_receipt": "ar.receipt.write",
    # workforce
    "flowforge.phase4a.routes:create_worker": "workforce.write",
    "flowforge.phase4a.routes:create_location": "workforce.write",
    "flowforge.phase4a.routes:assign": "workforce.write",
    "flowforge.phase4a.routes:compensation": "workforce.write",
    "flowforge.phase4a.routes:bank_account": "workforce.write",
    "flowforge.phase4a.routes:tax_profile": "workforce.write",
    "flowforge.phase4a.routes:benefit_plan": "workforce.write",
    "flowforge.phase4a.routes:enroll": "workforce.write",
    "flowforge.phase4a_stage2.routes:schedule": "workforce.write",
    "flowforge.phase4a_stage2.routes:time_entry": "workforce.write",
    "flowforge.phase4a_stage2.routes:approve_time": "workforce.approve",
    "flowforge.phase4a_stage2.routes:leave_type": "workforce.write",
    "flowforge.phase4a_stage2.routes:leave_request": "workforce.write",
    # payroll
    "flowforge.phase4a_stage2.routes:pay_group": "payroll.setup",
    "flowforge.phase4a_stage2.routes:pay_period": "payroll.setup",
    "flowforge.phase4a_stage3.routes:create_run": "payroll.run.write",
    "flowforge.phase4a_stage3.routes:calculate": "payroll.run.write",
    "flowforge.phase4a_stage3.routes:approve": "payroll.run.approve",
    "flowforge.phase4a_stage3.routes:post": "payroll.run.post",
    "flowforge.phase4a_stage3.routes:payment": "payroll.pay",
    "flowforge.phase4a_stage3.routes:reconcile": "payroll.reconcile",
    # tax
    "flowforge.phase4b.routes:jurisdiction": "tax.setup",
    "flowforge.phase4b.routes:rule": "tax.setup",
    "flowforge.phase4b.routes:election": "tax.setup",
    "flowforge.phase4b.routes:calculate": "tax.calculate",
    "flowforge.phase4b_stage2.routes:create_liability": "tax.liability.write",
    "flowforge.phase4b_stage2.routes:create_return": "tax.return.write",
    "flowforge.phase4b_stage2.routes:approve_return": "tax.return.approve",
    "flowforge.phase4b_stage2.routes:remit_return": "tax.remit",
    "flowforge.phase4b_stage2.routes:create_notice": "tax.notice.manage",
    "flowforge.phase4b_stage2.routes:resolve_notice": "tax.notice.manage",
    "flowforge.phase4b_stage2.routes:reconcile_tax": "tax.reconcile",
    # release completion: period close, tax authorities, liabilities from payroll
    "flowforge.release.admin_routes:list_periods": "gl.read",
    "flowforge.release.admin_routes:close_period": "gl.period.manage",
    "flowforge.release.admin_routes:reopen_period": "gl.period.manage",
    "flowforge.release.admin_routes:list_authorities": "tax.read",
    "flowforge.release.admin_routes:create_authority": "tax.setup",
    "flowforge.release.admin_routes:liabilities_from_payroll": "tax.liability.write",
    # release completion: read models
    "flowforge.release.read_routes:list_orders": "ar.read",
    "flowforge.release.read_routes:get_order": "ar.read",
    "flowforge.release.read_routes:ar_open_items": "ar.read",
    "flowforge.release.read_routes:ar_aging": "ar.read",
    "flowforge.release.read_routes:ap_open_items": "ap.read",
    "flowforge.release.read_routes:ap_aging": "ap.read",
    "flowforge.release.read_routes:get_payroll_run": "payroll.read",
    "flowforge.release.read_routes:list_tax_liabilities": "tax.read",
    "flowforge.release.read_routes:list_tax_returns": "tax.read",
}

_optional_bearer = HTTPBearer(auto_error=False)


def endpoint_key(endpoint: Any) -> str:
    return f"{getattr(endpoint, '__module__', '')}:{getattr(endpoint, '__qualname__', '')}"


async def load_access(principal: Principal) -> set[str] | None:
    """Permission codes of an active user in an active tenant; None if access is revoked."""
    from flowforge.db.session import SessionLocal

    async with SessionLocal() as session:
        session.info["tenant_id"] = principal.tenant_id
        session.info["user_id"] = principal.user_id
        active = (
            await session.execute(
                text(
                    "SELECT 1 FROM users u JOIN tenants t ON t.id = u.tenant_id"
                    " WHERE u.id = :u AND u.tenant_id = :t AND u.is_active AND NOT u.is_deleted"
                    " AND NOT t.is_deleted AND t.status = 'active'"
                ),
                {"u": principal.user_id, "t": principal.tenant_id},
            )
        ).first()
        if active is None:
            return None
        rows = await session.execute(
            text(
                "SELECT DISTINCT p.code FROM user_roles ur"
                " JOIN roles r ON r.id = ur.role_id AND r.tenant_id = ur.tenant_id"
                "  AND NOT r.is_deleted"
                " JOIN role_permissions rp ON rp.role_id = ur.role_id"
                "  AND rp.tenant_id = ur.tenant_id"
                " JOIN permissions p ON p.id = rp.permission_id"
                " WHERE ur.user_id = :u AND ur.tenant_id = :t"
            ),
            {"u": principal.user_id, "t": principal.tenant_id},
        )
        return {row[0] for row in rows}


async def enforce(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_bearer)],
) -> None:
    endpoint = request.scope.get("endpoint")
    module = getattr(endpoint, "__module__", "")
    if module not in RELEASE_MODULES:
        return  # extended modules keep their own authentication
    key = endpoint_key(endpoint)
    if key not in POLICY:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Endpoint has no authorization policy")
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    principal = current_principal(credentials)
    granted = await load_access(principal)
    if granted is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account or tenant is not active")
    required = POLICY[key]
    if required and required not in granted:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing permission: {required}")
    request.state.permissions = granted


async def sync_standard_roles() -> dict[str, int]:
    """Ensure the catalog and every tenant's standard roles hold the current permission sets.

    Additive only (never removes a role, grant or assignment), so it is safe on every
    start. Covers tenants created by import or restore after migrations ran, and new
    catalog codes added in later releases.
    """
    from flowforge.db.session import SessionLocal

    added = {"permissions": 0, "roles": 0, "grants": 0}
    async with SessionLocal() as session:
        for code, description in CATALOG.items():
            result = await session.execute(
                text(
                    "INSERT INTO permissions (id, code, description)"
                    " VALUES (gen_random_uuid(), :c, :d) ON CONFLICT (code) DO NOTHING"
                ),
                {"c": code, "d": description},
            )
            added["permissions"] += result.rowcount or 0  # type: ignore[attr-defined]
        await session.commit()
        tenant_ids = [row[0] for row in await session.execute(text("SELECT id FROM tenants"))]
    for tenant_id in tenant_ids:
        async with SessionLocal() as session:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)}
            )
            for role_name, codes in STANDARD_ROLES.items():
                result = await session.execute(
                    text(
                        "INSERT INTO roles (id, tenant_id, name, description, is_deleted)"
                        " VALUES (gen_random_uuid(), :t, :n, :d, false)"
                        " ON CONFLICT (tenant_id, name) DO NOTHING"
                    ),
                    {"t": tenant_id, "n": role_name, "d": f"Standard {role_name} role"},
                )
                added["roles"] += result.rowcount or 0  # type: ignore[attr-defined]
                result = await session.execute(
                    text(
                        "INSERT INTO role_permissions (role_id, permission_id, tenant_id)"
                        " SELECT r.id, p.id, r.tenant_id FROM roles r JOIN permissions p"
                        " ON p.code = ANY(:codes) WHERE r.tenant_id = :t AND r.name = :n"
                        " AND NOT r.is_deleted ON CONFLICT DO NOTHING"
                    ),
                    {"t": tenant_id, "n": role_name, "codes": sorted(codes)},
                )
                added["grants"] += result.rowcount or 0  # type: ignore[attr-defined]
            await session.commit()
    return added

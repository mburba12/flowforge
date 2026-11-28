"""Role-based access control for every API operation.

* CATALOG: every permission code with its description (seeded by migrations
  ff_rbac_001/ff_rbac_002 and kept current by sync_standard_roles at startup).
* STANDARD_ROLES: permission sets for the built-in roles created for every tenant.
* POLICY: the permission each release-scope endpoint requires, keyed by the endpoint
  function ("module:qualname") because nested include_router prefixes make route
  paths unreliable for matching.
* EXTENDED_POLICY: derived per operation for the extended domains by
  build_extended_policy(app) (read / write / approve per domain).
* enforce(): app-wide dependency. Except for PUBLIC endpoints it requires a valid
  token, an active user in an active tenant, and the mapped permission. An endpoint
  without a policy is denied (deny by default).
"""

import re
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.routing import APIRoute
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
    # extended domains (policy derived per operation by build_extended_policy)
    "integrations.read": "Read integration providers and connections",
    "crm.read": "Read leads, opportunities, quotes, campaigns and pricing",
    "crm.write": "Maintain leads, opportunities, quotes, activities, campaigns and pricing",
    "crm.approve": "Decide CRM transitions (win/lose, approve quotes)",
    "commerce.read": "Read requisitions, transfers, counts, shipments and returns",
    "commerce.write": "Create requisitions, reservations, transfers, receipts and shipments",
    "commerce.approve": "Approve requisitions, transfers and inventory counts",
    "finance.advanced.read": "Read close runs, budgets, assets, consolidations and controls",
    "finance.advanced.write": "Prepare accruals, allocations, recurring journals and budgets",
    "finance.advanced.approve": "Post, close, reverse, release and certify advanced finance work",
    "payroll.advanced.read": "Read payroll adjustments, filings, garnishments and year-end forms",
    "payroll.advanced.write": "Prepare payroll adjustments, imports, filings and payment batches",
    "payroll.advanced.approve": "Approve payroll adjustments, filings and payment batches",
    "billing.read": "Read plans, subscriptions, projects, billing runs and fixed assets",
    "billing.write": "Maintain plans, subscriptions, projects, time, expenses and usage",
    "billing.approve": "Execute billing runs, post project billing and depreciation",
    "manufacturing.read": "Read manufacturing and quality records",
    "manufacturing.write": "Create manufacturing and quality records and genealogy",
    "manufacturing.approve": "Approve, release and close manufacturing and quality records",
    "intelligence.read": "Search and read knowledge records and copilot proposals",
    "intelligence.write": "Create knowledge records, copilot proposals and upload inspections",
    "intelligence.approve": "Accept or reject copilot proposals",
    "operations.read": "Read operations runs",
    "operations.write": "Start and complete operations runs",
    "operations.approve": "Approve operations runs",
    "entities.read": "Read entities, relationships and lineage",
    "entities.write": "Create entities, relationships, lineage and match proposals",
    "entities.approve": "Approve entity merges",
    "governance.read": "Read entitlements, access reviews, delegations and controls",
    "governance.write": "Maintain entitlements, delegations, approval limits and SoD rules",
    "governance.approve": "Decide access reviews, revoke delegations and disable entitlements",
}

# Extended modules: module prefix -> permission domain. Longest prefix wins.
EXTENDED_DOMAINS: dict[str, str] = {
    "flowforge.crm_": "crm",
    "flowforge.commerce_": "commerce",
    "flowforge.finance.": "finance.advanced",
    "flowforge.finance_": "finance.advanced",
    "flowforge.phase3final.routes": "finance.advanced",
    "flowforge.phase4e.routes": "finance.advanced",
    "flowforge.foundation_": "governance",
    "flowforge.master_data.": "masterdata",
    "flowforge.workforce_": "workforce",
    "flowforge.payroll_tax_": "payroll.advanced",
    "flowforge.bg08_": "billing",
    "flowforge.bg09_": "manufacturing",
    "flowforge.bg10_": "intelligence",
    "flowforge.phase4f.routes": "intelligence",
    "flowforge.bg11_": "integrations",
    "flowforge.phase4c": "integrations",
    "flowforge.bg13_": "operations",
    "flowforge.phase4d.routes": "entities",
}
# domain -> (read, write, approve) permission codes
DOMAIN_CODES: dict[str, tuple[str, str, str]] = {
    "masterdata": ("masterdata.read", "masterdata.write", "masterdata.write"),
    "workforce": ("workforce.read", "workforce.write", "workforce.approve"),
    "integrations": ("integrations.read", "integrations.manage", "integrations.manage"),
    **{
        d: (f"{d}.read", f"{d}.write", f"{d}.approve")
        for d in (
            "crm",
            "commerce",
            "finance.advanced",
            "payroll.advanced",
            "billing",
            "manufacturing",
            "intelligence",
            "operations",
            "entities",
            "governance",
        )
    },
}
# Last path segments of operations that commit a decision (approve level).
APPROVE_SEGMENTS = {
    "approve",
    "post",
    "close",
    "reopen",
    "certify",
    "release",
    "reverse",
    "execute",
    "apply",
    "depreciate",
    "decide",
    "revoke",
    "disable",
    "merge",
}
# Generic state-change endpoints: approve level only when the requested target is a decision.
DECISION_SEGMENTS = {"action", "transition"}
DECISION_FIELDS = ("target", "stage", "action", "decision", "status", "to_status")
DECISION_VALUES = {
    "approve",
    "approved",
    "reject",
    "rejected",
    "post",
    "posted",
    "release",
    "released",
    "simulated_released",
    "close",
    "closed",
    "won",
    "lost",
    "accept",
    "accepted",
    "paid",
    "executed",
    "voided",
    "recalled",
    "activate",
    "terminate",
    "terminated",
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
# Extended domains: clerks prepare, approvers decide. Governance and integrations stay
# with owners and managers.
_ADMIN_DOMAINS = {"governance", "integrations"}
_APPROVE |= {
    codes[2] for d, codes in DOMAIN_CODES.items() if d not in _ADMIN_DOMAINS | {"masterdata"}
}
_CLERK_WRITE |= {codes[1] for d, codes in DOMAIN_CODES.items() if d not in _ADMIN_DOMAINS}

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

# Endpoints anyone may call without signing in.
PUBLIC: set[str] = {
    "flowforge.api.routes.auth:bootstrap",
    "flowforge.api.routes.auth:login",
    "flowforge.api.routes.health:health",
    "flowforge.support_feedback:submit_problem_report",
}
# Read-only module diagnostics (/phase*/status, /phase1b/health): static, no tenant data.
_DIAGNOSTIC_PATH = re.compile(r"^/phase[\w/]*/(status|health)$")
# Explicit choices for extended endpoints that the derivation would get wrong.
EXTENDED_OVERRIDES: dict[str, str] = {
    "flowforge.control_plane.router:capabilities": AUTHENTICATED,
    "flowforge.control_plane.router:capability": AUTHENTICATED,
    "flowforge.control_plane.router:readiness": AUTHENTICATED,
}

# Filled by build_extended_policy(app) once every router is included.
EXTENDED_POLICY: dict[str, str] = {}
DECISIONS: dict[str, tuple[str, str]] = {}  # endpoint key -> (write code, approve code)

_optional_bearer = HTTPBearer(auto_error=False)


def endpoint_key(endpoint: Any) -> str:
    return f"{getattr(endpoint, '__module__', '')}:{getattr(endpoint, '__qualname__', '')}"


def iter_api_routes(routes: list[Any]) -> list[APIRoute]:
    """All API routes, including those inside lazily included routers."""
    found: list[APIRoute] = []
    for route in routes:
        if isinstance(route, APIRoute):
            found.append(route)
        elif type(route).__name__ == "_IncludedRouter":
            found.extend(iter_api_routes(route.original_router.routes))
    return found


def extended_domain(module: str) -> str | None:
    matches = [prefix for prefix in EXTENDED_DOMAINS if module.startswith(prefix)]
    return EXTENDED_DOMAINS[max(matches, key=len)] if matches else None


def build_extended_policy(app: Any) -> dict[str, str]:
    """Derive the permission of every endpoint outside the release modules.

    GET -> domain read; operations whose last path segment commits a decision
    (approve, post, close, ...) -> domain approve; generic action/transition
    endpoints -> write, escalated to approve at request time for decision targets;
    everything else -> domain write. Diagnostics and PUBLIC endpoints need no
    permission. Endpoints of an unknown module get no policy and are denied.
    """
    EXTENDED_POLICY.clear()
    DECISIONS.clear()
    for route in iter_api_routes(list(app.routes)):
        module = route.endpoint.__module__
        key = endpoint_key(route.endpoint)
        methods = route.methods or set()
        if module in RELEASE_MODULES or key in PUBLIC:
            continue
        if methods <= {"GET", "HEAD"} and _DIAGNOSTIC_PATH.match(route.path):
            PUBLIC.add(key)
            continue
        if key in EXTENDED_OVERRIDES:
            EXTENDED_POLICY[key] = EXTENDED_OVERRIDES[key]
            continue
        domain = extended_domain(module)
        if domain is None:
            continue
        read, write, approve = DOMAIN_CODES[domain]
        segments = [s for s in route.path.split("/") if s and not s.startswith("{")]
        last = segments[-1] if segments else ""
        if methods <= {"GET", "HEAD"}:
            EXTENDED_POLICY[key] = read
        elif last in APPROVE_SEGMENTS:
            EXTENDED_POLICY[key] = approve
        else:
            EXTENDED_POLICY[key] = write
            if last in DECISION_SEGMENTS and approve != write:
                DECISIONS[key] = (write, approve)
    return EXTENDED_POLICY


async def _decision_requested(request: Request) -> bool:
    try:
        body = await request.json()
    except ValueError:
        return False
    if not isinstance(body, dict):
        return False
    return any(str(body.get(field, "")).lower() in DECISION_VALUES for field in DECISION_FIELDS)


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
    key = endpoint_key(endpoint)
    if key in PUBLIC:
        return
    required = POLICY.get(key, EXTENDED_POLICY.get(key))
    if required is None:
        # Deny by default: every operation must have an explicit or derived policy.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Endpoint has no authorization policy")
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    principal = current_principal(credentials)
    granted = await load_access(principal)
    if granted is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account or tenant is not active")
    if key in DECISIONS and await _decision_requested(request):
        required = DECISIONS[key][1]
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

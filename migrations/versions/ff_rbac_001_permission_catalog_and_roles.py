"""Seed the RBAC permission catalog and standard roles for every tenant.

Snapshot of flowforge.platform.authorization at revision time (migrations are
immutable; later catalog changes need a new revision). For each tenant it creates
any missing standard role (Owner, Manager, Approver, Clerk, Viewer) and grants that
role its permission set. Existing roles, assignments and grants are never removed.

Revision ID: ff_rbac_001
Revises: ff_seed_uom_001
"""

import json

from alembic import op
from sqlalchemy import text

revision = "ff_rbac_001"
down_revision = "ff_seed_uom_001"
branch_labels = None
depends_on = None

CATALOG: dict[str, str] = json.loads(
    r"""{
    "ap.invoice.post": "Post vendor invoices to the ledger",
    "ap.invoice.write": "Create and match vendor invoices",
    "ap.pay": "Pay AP open items",
    "ap.po.approve": "Approve purchase orders",
    "ap.po.write": "Create and submit purchase orders",
    "ap.read": "Read AP documents, open items and aging",
    "ap.receive": "Record goods receipts",
    "ap.reconcile": "Run AP reconciliation",
    "ap.vendor.write": "Create vendors",
    "ar.customer.write": "Create customers",
    "ar.order.fulfill": "Reserve, ship and invoice sales orders",
    "ar.order.write": "Create sales orders",
    "ar.read": "Read customers, orders, invoices, open items and aging",
    "ar.receipt.write": "Record customer receipts",
    "audit.read": "Read the audit trail",
    "business.read": "Browse business records (generic read-only browser)",
    "documents.manage": "Manage documents",
    "gl.journal.approve": "Approve journals",
    "gl.journal.post": "Post journals",
    "gl.journal.write": "Create journals",
    "gl.period.manage": "Create, close and reopen accounting periods",
    "gl.read": "Read ledgers, periods and trial balance",
    "gl.setup": "Create currencies, calendars, ledgers and accounts",
    "integrations.manage": "Manage integration connections",
    "inventory.setup": "Create products, warehouses and locations",
    "inventory.write": "Adjust inventory",
    "masterdata.read": "Read parties and organization units",
    "masterdata.write": "Create parties and organization units",
    "notifications.manage": "Create notifications",
    "payroll.pay": "Pay workers",
    "payroll.read": "Read payroll runs and results",
    "payroll.reconcile": "Reconcile payroll runs",
    "payroll.run.approve": "Approve payroll runs",
    "payroll.run.post": "Post payroll runs to the ledger",
    "payroll.run.write": "Create and calculate payroll runs",
    "payroll.setup": "Create pay groups and pay periods",
    "platform.tenants.create": "Create tenants (platform operators; no tenant role)",
    "roles.manage": "Create roles and set role permissions",
    "tax.calculate": "Run tax calculations",
    "tax.liability.write": "Create tax liabilities",
    "tax.notice.manage": "Record and resolve tax notices",
    "tax.read": "Read tax configuration, liabilities and returns",
    "tax.reconcile": "Reconcile tax accounts",
    "tax.remit": "Remit tax payments",
    "tax.return.approve": "Approve tax returns",
    "tax.return.write": "Create tax returns",
    "tax.setup": "Maintain jurisdictions, rules, authorities and worker elections",
    "tenant.manage": "Manage tenant settings",
    "tenant.read": "View own tenant",
    "users.manage": "Create, update, deactivate users and assign roles",
    "workflows.manage": "Manage workflow definitions",
    "workforce.approve": "Approve time entries",
    "workforce.read": "Read workers and workforce records",
    "workforce.write": "Maintain workers, compensation, profiles, schedules, time and leave"
}"""
)
STANDARD_ROLES: dict[str, list[str]] = json.loads(
    r"""{
    "Approver": [
        "ap.po.approve",
        "ap.read",
        "ar.read",
        "business.read",
        "gl.journal.approve",
        "gl.journal.post",
        "gl.read",
        "masterdata.read",
        "payroll.read",
        "payroll.run.approve",
        "tax.read",
        "tax.return.approve",
        "tenant.read",
        "workforce.approve",
        "workforce.read"
    ],
    "Clerk": [
        "ap.invoice.write",
        "ap.po.write",
        "ap.read",
        "ap.receive",
        "ap.vendor.write",
        "ar.customer.write",
        "ar.order.fulfill",
        "ar.order.write",
        "ar.read",
        "ar.receipt.write",
        "business.read",
        "documents.manage",
        "gl.journal.write",
        "gl.read",
        "inventory.write",
        "masterdata.read",
        "masterdata.write",
        "notifications.manage",
        "payroll.read",
        "payroll.run.write",
        "tax.calculate",
        "tax.liability.write",
        "tax.notice.manage",
        "tax.read",
        "tax.return.write",
        "tenant.read",
        "workforce.read",
        "workforce.write"
    ],
    "Manager": [
        "ap.invoice.post",
        "ap.invoice.write",
        "ap.pay",
        "ap.po.approve",
        "ap.po.write",
        "ap.read",
        "ap.receive",
        "ap.reconcile",
        "ap.vendor.write",
        "ar.customer.write",
        "ar.order.fulfill",
        "ar.order.write",
        "ar.read",
        "ar.receipt.write",
        "audit.read",
        "business.read",
        "documents.manage",
        "gl.journal.approve",
        "gl.journal.post",
        "gl.journal.write",
        "gl.period.manage",
        "gl.read",
        "gl.setup",
        "integrations.manage",
        "inventory.setup",
        "inventory.write",
        "masterdata.read",
        "masterdata.write",
        "notifications.manage",
        "payroll.pay",
        "payroll.read",
        "payroll.reconcile",
        "payroll.run.approve",
        "payroll.run.post",
        "payroll.run.write",
        "payroll.setup",
        "tax.calculate",
        "tax.liability.write",
        "tax.notice.manage",
        "tax.read",
        "tax.reconcile",
        "tax.remit",
        "tax.return.approve",
        "tax.return.write",
        "tax.setup",
        "tenant.read",
        "workflows.manage",
        "workforce.approve",
        "workforce.read",
        "workforce.write"
    ],
    "Owner": [
        "ap.invoice.post",
        "ap.invoice.write",
        "ap.pay",
        "ap.po.approve",
        "ap.po.write",
        "ap.read",
        "ap.receive",
        "ap.reconcile",
        "ap.vendor.write",
        "ar.customer.write",
        "ar.order.fulfill",
        "ar.order.write",
        "ar.read",
        "ar.receipt.write",
        "audit.read",
        "business.read",
        "documents.manage",
        "gl.journal.approve",
        "gl.journal.post",
        "gl.journal.write",
        "gl.period.manage",
        "gl.read",
        "gl.setup",
        "integrations.manage",
        "inventory.setup",
        "inventory.write",
        "masterdata.read",
        "masterdata.write",
        "notifications.manage",
        "payroll.pay",
        "payroll.read",
        "payroll.reconcile",
        "payroll.run.approve",
        "payroll.run.post",
        "payroll.run.write",
        "payroll.setup",
        "roles.manage",
        "tax.calculate",
        "tax.liability.write",
        "tax.notice.manage",
        "tax.read",
        "tax.reconcile",
        "tax.remit",
        "tax.return.approve",
        "tax.return.write",
        "tax.setup",
        "tenant.manage",
        "tenant.read",
        "users.manage",
        "workflows.manage",
        "workforce.approve",
        "workforce.read",
        "workforce.write"
    ],
    "Viewer": [
        "ap.read",
        "ar.read",
        "business.read",
        "gl.read",
        "masterdata.read",
        "payroll.read",
        "tax.read",
        "tenant.read",
        "workforce.read"
    ]
}"""
)


def upgrade() -> None:
    bind = op.get_bind()
    for code, description in CATALOG.items():
        bind.execute(
            text(
                "INSERT INTO permissions (id, code, description) VALUES (gen_random_uuid(), :c, :d)"
                " ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description"
            ),
            {"c": code, "d": description},
        )
    tenants = [row[0] for row in bind.execute(text("SELECT id FROM tenants"))]
    for tenant_id in tenants:
        for role_name, codes in STANDARD_ROLES.items():
            bind.execute(
                text(
                    "INSERT INTO roles (id, tenant_id, name, description, is_deleted)"
                    " VALUES (gen_random_uuid(), :t, :n, :d, false)"
                    " ON CONFLICT (tenant_id, name) DO NOTHING"
                ),
                {"t": tenant_id, "n": role_name, "d": f"Standard {role_name} role"},
            )
            bind.execute(
                text(
                    "INSERT INTO role_permissions (role_id, permission_id, tenant_id)"
                    " SELECT r.id, p.id, r.tenant_id FROM roles r JOIN permissions p"
                    " ON p.code = ANY(:codes) WHERE r.tenant_id = :t AND r.name = :n"
                    " ON CONFLICT DO NOTHING"
                ),
                {"t": tenant_id, "n": role_name, "codes": codes},
            )


def downgrade() -> None:
    # Grants and roles are retained: removing them could lock users out.
    pass

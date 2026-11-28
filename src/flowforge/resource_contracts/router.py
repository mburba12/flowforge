"""Generic read-only browsing of tenant-owned tables.

Interim contract used by the frontend BusinessWorkspace until each domain is
served by its canonical typed routes. Every query is explicitly scoped to the
caller's tenant (the runtime database does not enforce RLS), and the router is
read-only: business mutations must go through domain services that validate
state transitions, permissions, and write audit records.
"""

import asyncio
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

router = APIRouter(prefix="/api/v1/business", tags=["business-resources"])
Db = Annotated[AsyncSession, Depends(get_tenant_db)]
Caller = Annotated[Principal, Depends(current_principal)]

ALIASES: dict[str, tuple[str, ...]] = {
    "vendors": ("vendor_profiles", "vendors"),
    "purchase-orders": ("purchase_orders",),
    "goods-receipts": ("goods_receipts",),
    "vendor-invoices": ("vendor_invoices",),
    "customers": ("customer_profiles", "customers"),
    "receipts": ("customer_receipts", "receipts"),
    "products": ("products",),
    "warehouses": ("warehouses",),
    "locations": ("warehouse_locations", "locations", "work_locations"),
    "inventory": ("inventory_balances", "inventory_items", "stock_balances"),
    "orders": ("sales_orders", "orders"),
    "workers": ("worker_profiles", "workforce_workers", "workers"),
    "work-locations": ("work_locations",),
    "time-entries": ("time_entries",),
    "work-schedules": ("work_schedules", "schedules"),
    "leave-requests": ("leave_requests",),
    "benefit-plans": ("benefit_plans",),
    "pay-groups": ("pay_groups",),
    "pay-periods": ("pay_periods",),
    "payroll-runs": ("payroll_runs", "workforce_payroll_runs"),
    "jurisdictions": ("tax_jurisdictions", "jurisdictions"),
    "tax-rules": ("tax_rules",),
    "liabilities": ("tax_liabilities",),
    "returns": ("tax_returns",),
    "notices": ("tax_notices",),
    "ledgers": ("ledgers",),
    "accounts": ("accounts",),
    "journals": ("journal_entries", "journals"),
    "connections": ("connected_bank_accounts", "integration_connections"),
    "transactions": ("bank_transactions", "transactions"),
    "reconciliations": (
        "finance_reconciliation_sessions",
        "reconciliation_runs",
        "reconciliations",
    ),
    "integration-connections": ("integration_connections", "provider_connections"),
    "integration-sync-runs": ("integration_sync_runs", "sync_runs"),
    "webhook-deliveries": ("webhook_deliveries",),
    "documents": ("documents",),
    "entities": ("canonical_entities", "entities"),
    "organizations": ("party_organizations", "organizations"),
    "people": ("party_people", "people"),
    "approvals": ("approval_requests", "approvals"),
    "work-items": ("work_queue_items", "workflow_tasks", "work_items"),
    "audit": ("audit_entries", "audit_events"),
    "reports": ("report_definitions", "reports"),
    "report-runs": ("report_runs",),
    "users": ("users",),
    "roles": ("roles",),
    "permissions": ("permissions",),
    "notifications": ("notifications",),
    "support-cases": ("support_cases", "phase5a_support_cases"),
    "copilot-conversations": ("copilot_conversations",),
    "relationships": ("party_relationships", "entity_relationships"),
    "sync-runs": ("bank_sync_runs",),
    "inventory-transfers": ("commerce_inventory_transfers_final",),
    "inventory-counts": ("commerce_inventory_counts_final",),
}

SENSITIVE_MARKERS = ("password", "secret", "token", "credential", "hash")

_table_cache: dict[str, Table] | None = None
_table_cache_lock = asyncio.Lock()


def _reflect_tenant_tables(sync_session: Session) -> dict[str, Table]:
    metadata = MetaData()
    metadata.reflect(bind=sync_session.connection(), schema="public")
    return {
        table.name: table
        for table in metadata.tables.values()
        if table.schema == "public" and "tenant_id" in table.c
    }


async def _tables(db: AsyncSession) -> dict[str, Table]:
    """Reflect public tenant-owned tables once per process.

    Reflection is synchronous SQLAlchemy work, so it must run through
    AsyncSession.run_sync; calling it directly raises MissingGreenlet.
    The schema only changes through migrations, which restart the API.
    """
    global _table_cache
    if _table_cache is None:
        async with _table_cache_lock:
            if _table_cache is None:
                _table_cache = await db.run_sync(_reflect_tenant_tables)
    return _table_cache


async def _resolve(resource: str, db: AsyncSession) -> Table:
    available = await _tables(db)
    candidates = ALIASES.get(resource, (resource.replace("-", "_"),))
    for name in candidates:
        table = available.get(name)
        if table is not None:
            return table
    raise HTTPException(404, f"Resource is not available: {resource}")


def _clean(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _row(row: Any) -> dict[str, Any]:
    return {
        key: _clean(value)
        for key, value in row._mapping.items()
        if not any(marker in key.lower() for marker in SENSITIVE_MARKERS)
    }


def _visible_columns(table: Table) -> list[Any]:
    return [
        column
        for column in table.columns
        if not any(marker in column.name.lower() for marker in SENSITIVE_MARKERS)
    ]


@router.get("/resources")
async def resources(db: Db, caller: Caller) -> list[dict[str, Any]]:
    available = await _tables(db)
    result = []
    for alias, candidates in sorted(ALIASES.items()):
        table = next((available[name] for name in candidates if name in available), None)
        if table is not None:
            result.append(
                {
                    "resource": alias,
                    "table": table.name,
                    "columns": [column.name for column in _visible_columns(table)],
                }
            )
    return result


@router.get("/{resource}")
async def list_records(
    resource: str,
    db: Db,
    caller: Caller,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    field: str | None = Query(None, max_length=63),
    value: str | None = Query(None, max_length=200),
) -> dict[str, Any]:
    table = await _resolve(resource, db)
    tenant_filter = table.c.tenant_id == caller.tenant_id
    if field is not None:
        # Single equality filter on a visible column (validated against the table).
        visible = {column.name for column in _visible_columns(table)}
        if field not in visible or value is None:
            raise HTTPException(422, f"Cannot filter {resource} by {field!r}")
        column = table.c[field]
        try:
            typed: Any = UUID(value) if str(column.type).upper() == "UUID" else value
        except ValueError as exc:
            raise HTTPException(422, f"Invalid value for {field}") from exc
        tenant_filter = tenant_filter & (column == typed)
    total = await db.scalar(select(func.count()).select_from(table).where(tenant_filter))
    order: list[Any] = [table.c.created_at.desc()] if "created_at" in table.c else []
    if "id" in table.c:
        order.append(table.c.id)
    result = await db.execute(
        select(*_visible_columns(table))
        .where(tenant_filter)
        .order_by(*order)
        .limit(limit)
        .offset(offset)
    )
    return {"resource": resource, "total": total or 0, "items": [_row(row) for row in result]}


@router.get("/{resource}/{record_id}")
async def get_record(resource: str, record_id: str, db: Db, caller: Caller) -> dict[str, Any]:
    table = await _resolve(resource, db)
    if "id" not in table.c:
        raise HTTPException(404, "Resource has no record identifier")
    try:
        key = UUID(record_id)
    except ValueError as exc:
        raise HTTPException(404, "Record not found") from exc
    result = await db.execute(
        select(*_visible_columns(table)).where(
            table.c.id == key,
            table.c.tenant_id == caller.tenant_id,
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(404, "Record not found")
    return _row(row)

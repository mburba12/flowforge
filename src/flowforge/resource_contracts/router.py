from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.db.session import get_tenant_db

router = APIRouter(prefix="/api/v1/business", tags=["business-resources"])
Db = Annotated[AsyncSession, Depends(get_tenant_db)]

ALIASES: dict[str, tuple[str, ...]] = {
    "vendors": ("vendors",),
    "purchase-orders": ("purchase_orders",),
    "goods-receipts": ("goods_receipts",),
    "vendor-invoices": ("vendor_invoices",),
    "customers": ("customers",),
    "receipts": ("customer_receipts", "receipts"),
    "products": ("products",),
    "warehouses": ("warehouses",),
    "locations": ("warehouse_locations", "locations", "work_locations"),
    "inventory": ("inventory_balances", "inventory_items", "stock_balances"),
    "orders": ("sales_orders", "orders"),
    "workers": ("workers",),
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
    "journals": ("journals",),
    "connections": ("connected_bank_accounts", "integration_connections"),
    "transactions": ("bank_transactions", "transactions"),
    "reconciliations": ("reconciliation_runs", "reconciliations"),
    "integration-connections": ("integration_connections", "provider_connections"),
    "integration-sync-runs": ("integration_sync_runs", "sync_runs"),
    "webhook-deliveries": ("webhook_deliveries",),
    "documents": ("documents",),
    "entities": ("entities",),
    "organizations": ("organizations",),
    "people": ("people",),
    "approvals": ("approval_requests", "approvals"),
    "work-items": ("work_queue_items", "workflow_tasks", "work_items"),
    "audit": ("audit_events",),
    "reports": ("report_definitions", "reports"),
    "report-runs": ("report_runs",),
    "users": ("users",),
    "roles": ("roles",),
    "permissions": ("permissions",),
    "notifications": ("notifications",),
    "support-cases": ("support_cases", "phase5a_support_cases"),
    "copilot-conversations": ("copilot_conversations",),
}

READ_ONLY_COLUMNS = {"id", "tenant_id", "created_at", "created_by"}
SENSITIVE_MARKERS = ("password", "secret", "token", "credential", "hash")


def _tables(db: AsyncSession) -> dict[str, Table]:
    metadata = MetaData()
    metadata.reflect(bind=db.sync_session.connection(), schema="public")
    return {
        table.name: table
        for table in metadata.tables.values()
        if "tenant_id" in table.c
    }


def _resolve(resource: str, db: AsyncSession) -> Table:
    available = _tables(db)
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


@router.get("/resources")
async def resources(db: Db) -> list[dict[str, Any]]:
    available = _tables(db)
    result = []
    for alias, candidates in sorted(ALIASES.items()):
        table = next((available.get(name) for name in candidates if name in available), None)
        if table is not None:
            result.append(
                {
                    "resource": alias,
                    "table": table.name,
                    "columns": [
                        column.name
                        for column in table.columns
                        if not any(marker in column.name.lower() for marker in SENSITIVE_MARKERS)
                    ],
                }
            )
    return result


@router.get("/{resource}")
async def list_records(
    resource: str,
    db: Db,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    table = _resolve(resource, db)
    total = await db.scalar(select(func.count()).select_from(table))
    result = await db.execute(select(table).limit(limit).offset(offset))
    return {"resource": resource, "total": total or 0, "items": [_row(row) for row in result]}


@router.get("/{resource}/{record_id}")
async def get_record(resource: str, record_id: str, db: Db) -> dict[str, Any]:
    table = _resolve(resource, db)
    if "id" not in table.c:
        raise HTTPException(404, "Resource has no record identifier")
    result = await db.execute(select(table).where(table.c.id == record_id))
    row = result.first()
    if row is None:
        raise HTTPException(404, "Record not found")
    return _row(row)


@router.patch("/{resource}/{record_id}")
async def update_record(
    resource: str,
    record_id: str,
    payload: dict[str, Any],
    db: Db,
) -> dict[str, Any]:
    table = _resolve(resource, db)
    if "id" not in table.c:
        raise HTTPException(404, "Resource has no record identifier")
    editable = {
        column.name
        for column in table.columns
        if column.name not in READ_ONLY_COLUMNS
        and not any(marker in column.name.lower() for marker in SENSITIVE_MARKERS)
    }
    changes = {key: value for key, value in payload.items() if key in editable}
    if not changes:
        raise HTTPException(422, "No editable fields supplied")
    existing = await db.execute(
        select(table.c.id).where(table.c.id == record_id)
    )
    if existing.first() is None:
        raise HTTPException(404, "Record not found")
    await db.execute(
        update(table).where(table.c.id == record_id).values(**changes)
    )
    await db.commit()
    return await get_record(resource, record_id, db)

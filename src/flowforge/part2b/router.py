from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Table, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.db.session import get_tenant_db
from flowforge.resource_contracts.router import tenant_tables

router = APIRouter(prefix="/api/v1/platform", tags=["part2b-platform"])
Db = Annotated[AsyncSession, Depends(get_tenant_db)]
RESOURCE_MAP = {
    "work-items": ("work_queue_items", "workflow_tasks"),
    "approvals": ("approval_requests", "workflow_tasks"),
    "integrations": ("provider_registrations", "integrations"),
    "documents": ("documents",),
    "users": ("users",),
    "roles": ("roles",),
    "audit": ("audit_events",),
    "notifications": ("notifications",),
    "support": ("support_cases", "phase5a_support_cases"),
    "billing": ("phase5a_tenant_subscriptions",),
}


async def tables(db: AsyncSession) -> dict[str, Table]:
    return await tenant_tables(db)


async def resource_table(name: str, db: AsyncSession) -> Table:
    available = await tables(db)
    for candidate in RESOURCE_MAP.get(name, ()):
        table = available.get(candidate)
        if table is not None and "tenant_id" in table.c:
            return table
    raise HTTPException(404, f"Resource not available: {name}")


def value(item: Any) -> Any:
    if item is None or isinstance(item, (str, int, float, bool)):
        return item
    if hasattr(item, "isoformat"):
        return item.isoformat()
    return str(item)


def output(row: Any) -> dict[str, Any]:
    return {key: value(item) for key, item in row._mapping.items()}


@router.get("/{resource}")
async def list_resource(
    resource: str, db: Db, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)
) -> dict[str, Any]:
    table = await resource_table(resource, db)
    total = await db.scalar(select(func.count()).select_from(table))
    rows = await db.execute(select(table).limit(limit).offset(offset))
    return {"total": total or 0, "items": [output(row) for row in rows]}


@router.get("/{resource}/{record_id}")
async def get_resource(resource: str, record_id: str, db: Db) -> dict[str, Any]:
    table = await resource_table(resource, db)
    if "id" not in table.c:
        raise HTTPException(404, "Resource has no record identifier")
    row = (await db.execute(select(table).where(table.c.id == record_id))).first()
    if row is None:
        raise HTTPException(404, "Record not found")
    return output(row)


@router.patch("/{resource}/{record_id}")
async def patch_resource(
    resource: str, record_id: str, payload: dict[str, Any], db: Db
) -> dict[str, Any]:
    table = await resource_table(resource, db)
    allowed = {
        column.name
        for column in table.columns
        if column.name not in {"id", "tenant_id", "created_at"}
    }
    changes = {key: item for key, item in payload.items() if key in allowed}
    if not changes:
        raise HTTPException(422, "No editable fields supplied")
    await db.execute(update(table).where(table.c.id == record_id).values(**changes))
    await db.commit()
    return {"id": record_id, "status": "updated"}


@router.get("/search/all")
async def search_all(q: str, db: Db, limit: int = Query(25, ge=1, le=100)) -> dict[str, Any]:
    found: list[dict[str, Any]] = []
    for name in RESOURCE_MAP:
        try:
            table = await resource_table(name, db)
        except HTTPException:
            continue
        text_columns = [
            column
            for column in table.columns
            if str(column.type).lower().startswith(("varchar", "text"))
        ]
        if not text_columns:
            continue
        clause = or_(*[column.ilike(f"%{q}%") for column in text_columns])
        rows = await db.execute(select(table).where(clause).limit(limit))
        found.extend({"resource": name, **output(row)} for row in rows)
        if len(found) >= limit:
            break
    return {"items": found[:limit]}

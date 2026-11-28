from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Table, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.db.session import get_tenant_db
from flowforge.resource_contracts.router import tenant_tables

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])
Db = Annotated[AsyncSession, Depends(get_tenant_db)]
BLOCKED = {"alembic_version", "tenants"}


async def public_tables(db: AsyncSession) -> dict[str, Table]:
    available = await tenant_tables(db)
    return {name: table for name, table in available.items() if name not in BLOCKED}


def clean(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


@router.get("/tables")
async def tables(db: Db) -> list[dict[str, Any]]:
    available = await public_tables(db)
    return [
        {"name": name, "columns": [column.name for column in table.columns]}
        for name, table in sorted(available.items())
    ]


@router.get("/tables/{table_name}/records")
async def records(
    table_name: str,
    db: Db,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    table = (await public_tables(db)).get(table_name)
    if table is None:
        raise HTTPException(404, "Unknown tenant resource")
    total = await db.scalar(select(func.count()).select_from(table))
    result = await db.execute(select(table).limit(limit).offset(offset))
    items = [{key: clean(value) for key, value in row._mapping.items()} for row in result]
    return {"table": table_name, "total": total or 0, "items": items}

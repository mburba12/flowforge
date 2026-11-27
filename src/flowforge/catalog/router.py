from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.db.session import get_tenant_db

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])
Db = Annotated[AsyncSession, Depends(get_tenant_db)]
BLOCKED = {"alembic_version", "tenants"}


def public_tables(db: AsyncSession) -> dict[str, Table]:
    metadata = MetaData()
    connection = db.sync_session.connection()
    metadata.reflect(bind=connection, schema="public")
    return {
        table.name: table
        for table in metadata.tables.values()
        if table.name not in BLOCKED and "tenant_id" in table.c
    }


def clean(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


@router.get("/tables")
async def tables(db: Db) -> list[dict[str, Any]]:
    available = public_tables(db)
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
    table = public_tables(db).get(table_name)
    if table is None:
        raise HTTPException(404, "Unknown tenant resource")
    total = await db.scalar(select(func.count()).select_from(table))
    result = await db.execute(select(table).limit(limit).offset(offset))
    items = [
        {key: clean(value) for key, value in row._mapping.items()}
        for row in result
    ]
    return {"table": table_name, "total": total or 0, "items": items}

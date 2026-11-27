from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.db.session import get_tenant_db

router = APIRouter(prefix="/api/v1/resources", tags=["part2a-resources"])
Db = Annotated[AsyncSession, Depends(get_tenant_db)]


def _tables(db: AsyncSession) -> dict[str, Table]:
    metadata = MetaData()
    metadata.reflect(
        bind=db.sync_session.connection(),
        schema="public",
    )
    return {table.name: table for table in metadata.tables.values() if "tenant_id" in table.c}


def _value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


@router.get("/{resource}")
async def list_resource(
    resource: str,
    db: Db,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    table = _tables(db).get(resource)
    if table is None:
        raise HTTPException(404, "Unknown resource")

    total = await db.scalar(select(func.count()).select_from(table))
    rows = await db.execute(select(table).limit(limit).offset(offset))
    items = [{key: _value(value) for key, value in row._mapping.items()} for row in rows]
    return {
        "total": total or 0,
        "items": items,
    }


@router.get("/{resource}/{record_id}")
async def get_resource(
    resource: str,
    record_id: str,
    db: Db,
) -> dict[str, Any]:
    table = _tables(db).get(resource)
    if table is None or "id" not in table.c:
        raise HTTPException(404, "Unknown resource")

    row = (await db.execute(select(table).where(table.c.id == record_id))).first()

    if row is None:
        raise HTTPException(404, "Record not found")

    return {key: _value(value) for key, value in row._mapping.items()}

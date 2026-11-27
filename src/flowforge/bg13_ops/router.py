import json
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .models import OperationalRun
from .schemas import RunComplete, RunCreate

router = APIRouter(prefix="/api/v2/bg13", tags=["bg13-operations"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


@router.post("/runs", status_code=201)
async def create(b: RunCreate, p: P, db: D) -> Any:
    x = OperationalRun(
        tenant_id=p.tenant_id,
        run_type=b.run_type,
        requested_by=p.user_id,
        evidence_json=json.dumps(b.evidence),
    )
    db.add(x)
    await db.commit()
    return x


@router.post("/runs/{id}/complete")
async def complete(id: UUID, b: RunComplete, p: P, db: D) -> Any:
    x = await db.scalar(
        select(OperationalRun).where(
            OperationalRun.id == id, OperationalRun.tenant_id == p.tenant_id
        )
    )
    if not x:
        raise HTTPException(404, "Run not found")
    x.status = b.status
    x.result_json = json.dumps(b.result)
    x.completed_at = datetime.now(UTC)
    await db.commit()
    return x

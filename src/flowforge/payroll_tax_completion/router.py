from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *
from .schemas import *
from .service import CompletionService

router = APIRouter(prefix="/api/v2/payroll-tax/completion", tags=["payroll-tax-completion"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D):
    return CompletionService(db, TenantContext(p.tenant_id, p.user_id))


def fail(e):
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/retro", status_code=201)
async def retro(b: RetroCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.retro(b)


@router.post("/garnishments", status_code=201)
async def garnishment(b: GarnishmentCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.save(
        GarnishmentOrder(tenant_id=s.ctx.tenant_id, **b.model_dump()), "garnishment"
    )


@router.post("/payment-batches", status_code=201)
async def batch(b: BatchCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.batch(b)


@router.post("/payment-batches/{id}/action")
async def batch_action(id: UUID, b: BatchAction, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.batch_action(id, b.target, b.idempotency_key)
    except Exception as e:
        raise fail(e) from e


@router.post("/year-end-forms", status_code=201)
async def year_end(b: YearEndCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.save(YearEndForm(tenant_id=s.ctx.tenant_id, **b.model_dump()), "year_end_form")


@router.post("/filing-submissions", status_code=201)
async def filing(b: FilingSubmissionCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.filing(b)

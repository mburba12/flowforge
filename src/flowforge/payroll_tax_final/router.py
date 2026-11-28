from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405
from .service import PayrollTaxService

router = APIRouter(prefix="/api/v2/payroll-tax/final", tags=["payroll-tax-final"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D) -> Any:
    return PayrollTaxService(db, TenantContext(p.tenant_id, p.user_id))


def fail(e) -> Any:
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/adjustments", status_code=201)
async def adjustment(b: AdjustmentCreate, s: Annotated[PayrollTaxService, Depends(svc)]):
    return await s.save(
        PayrollAdjustment(tenant_id=s.ctx.tenant_id, **b.model_dump()), "payroll_adjustment"
    )


@router.post("/adjustments/{id}/action")
async def adjustment_action(id: UUID, b: Action, s: Annotated[PayrollTaxService, Depends(svc)]):
    try:
        return await s.adjustment_action(id, b.target, b.idempotency_key)
    except Exception as e:
        raise fail(e) from e


@router.post("/imports", status_code=201)
async def imports(b: ImportCreate, s: Annotated[PayrollTaxService, Depends(svc)]):
    return await s.save(
        PayrollImport(tenant_id=s.ctx.tenant_id, **b.model_dump()), "payroll_import"
    )


@router.post("/parallel-runs", status_code=201)
async def parallel(b: ParallelCreate, s: Annotated[PayrollTaxService, Depends(svc)]):
    return await s.parallel(b)


@router.post("/tax-amendments", status_code=201)
async def amendment(b: AmendmentCreate, s: Annotated[PayrollTaxService, Depends(svc)]):
    return await s.save(TaxAmendment(tenant_id=s.ctx.tenant_id, **b.model_dump()), "tax_amendment")


@router.post("/filing-artifacts", status_code=201)
async def artifact(b: FilingArtifactCreate, s: Annotated[PayrollTaxService, Depends(svc)]):
    return await s.save(
        FilingArtifact(tenant_id=s.ctx.tenant_id, **b.model_dump()), "filing_artifact"
    )


@router.get("/runs/{run_id}/negative-net-check")
async def netcheck(run_id: UUID, s: Annotated[PayrollTaxService, Depends(svc)]):
    return await s.negative_net_check(run_id)


@router.get("/dashboard")
async def dashboard(s: Annotated[PayrollTaxService, Depends(svc)]):
    return await s.dashboard()

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405
from .service import FinanceAdvancedService

router = APIRouter(prefix="/api/v2/finance/advanced", tags=["finance-advanced"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D):
    return FinanceAdvancedService(db, TenantContext(p.tenant_id, p.user_id))


@router.post("/close-runs", status_code=201)
async def close_run(b: CloseRunCreate, s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.close_run(b)


@router.get("/close-runs")
async def close_runs(s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.list(CloseRun)


@router.post("/recurring-journals", status_code=201)
async def recurring(b: RecurringJournalCreate, s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.recurring(b)


@router.get("/recurring-journals")
async def recurrings(s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.list(RecurringJournal)


@router.post("/payment-batches", status_code=201)
async def batch(b: PaymentBatchCreate, s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.payment_batch(b)


@router.get("/payment-batches")
async def batches(s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.list(PaymentBatch)


@router.post("/reconciliations", status_code=201)
async def recon(b: ReconciliationCreate, s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.reconciliation(b)


@router.get("/reconciliations")
async def recons(s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.list(ReconciliationSession)


@router.post("/budgets", status_code=201)
async def budget(b: BudgetVersionCreate, s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.budget(b)


@router.post("/budgets/{version_id}/lines", status_code=201)
async def budget_line(
    version_id: UUID, b: BudgetLineCreate, s: Annotated[FinanceAdvancedService, Depends(svc)]
):
    try:
        return await s.budget_line(version_id, b)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except PermissionError as e:
        raise HTTPException(409, str(e)) from e


@router.post("/consolidations", status_code=201)
async def consolidation(b: ConsolidationCreate, s: Annotated[FinanceAdvancedService, Depends(svc)]):
    return await s.consolidation(b)


@router.post("/assets", status_code=201)
async def asset(b: AssetCreate, s: Annotated[FinanceAdvancedService, Depends(svc)]):
    try:
        return await s.asset(b)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.post("/assets/{asset_id}/depreciate")
async def depreciate(asset_id: UUID, s: Annotated[FinanceAdvancedService, Depends(svc)]):
    try:
        return await s.depreciate(asset_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e

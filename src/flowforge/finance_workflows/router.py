from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .schemas import CloseAssessmentRequest, ReconciliationAssessmentRequest
from .service import FinanceWorkflowService

router = APIRouter(prefix="/api/v2/finance/workflows", tags=["finance-workflows"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D) -> FinanceWorkflowService:
    return FinanceWorkflowService(db, TenantContext(p.tenant_id, p.user_id))


@router.get("/procure-to-pay")
async def p2p(s: Annotated[FinanceWorkflowService, Depends(svc)]):
    return await s.procure_to_pay()


@router.get("/order-to-cash")
async def o2c(s: Annotated[FinanceWorkflowService, Depends(svc)]):
    return await s.order_to_cash()


@router.post("/period-close/assess")
async def close(body: CloseAssessmentRequest, s: Annotated[FinanceWorkflowService, Depends(svc)]):
    try:
        return await s.close_assessment(body.ledger_id, body.period_id, body.tolerance)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/reconcile")
async def reconcile(
    body: ReconciliationAssessmentRequest, s: Annotated[FinanceWorkflowService, Depends(svc)]
):
    return s.reconcile(
        body.source_balance, body.target_balance, body.tolerance, body.source_name, body.target_name
    )


@router.get("/health")
async def health(s: Annotated[FinanceWorkflowService, Depends(svc)]):
    return await s.finance_health()

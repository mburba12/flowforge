from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405
from .service import CompletionService

router = APIRouter(prefix="/api/v2/finance/completion", tags=["finance-completion"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D) -> Any:
    return CompletionService(db, TenantContext(p.tenant_id, p.user_id))


def err(e) -> Any:
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/accruals", status_code=201)
async def accrual(b: AccrualCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.save(
        AccrualDefinition(tenant_id=s.ctx.tenant_id, **b.model_dump()), "accrual_definition"
    )


@router.post("/allocations", status_code=201)
async def allocation(b: AllocationCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.save(
        AllocationDefinition(tenant_id=s.ctx.tenant_id, **b.model_dump()), "allocation_definition"
    )


@router.post("/recurring-journals/{rid}/execute")
async def recurring(rid: UUID, b: ExecuteRequest, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.execute_recurring(rid, b.idempotency_key)
    except Exception as e:
        raise err(e) from e


@router.post("/close-runs/{cid}/close")
async def close(cid: UUID, b: ExecuteRequest, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.close_period(cid, b.idempotency_key)
    except Exception as e:
        raise err(e) from e


@router.post("/close-runs/{cid}/reopen")
async def reopen(cid: UUID, b: ExecuteRequest, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.reopen_period(cid, b.idempotency_key)
    except Exception as e:
        raise err(e) from e


@router.post("/payment-batches/{bid}/items", status_code=201)
async def payment_item(
    bid: UUID, b: PaymentItemCreate, s: Annotated[CompletionService, Depends(svc)]
):
    return await s.save(
        PaymentBatchItem(tenant_id=s.ctx.tenant_id, batch_id=bid, **b.model_dump()),
        "payment_batch_item",
    )


@router.post("/payment-batches/{bid}/release")
async def release(bid: UUID, b: ExecuteRequest, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.release_batch(bid, b.idempotency_key)
    except Exception as e:
        raise err(e) from e


@router.post("/reconciliations/{sid}/items", status_code=201)
async def recon_item(
    sid: UUID, b: ReconciliationItemCreate, s: Annotated[CompletionService, Depends(svc)]
):
    return await s.save(
        ReconciliationItem(tenant_id=s.ctx.tenant_id, session_id=sid, **b.model_dump()),
        "reconciliation_item",
    )


@router.post("/reconciliations/{sid}/certify")
async def certify(sid: UUID, b: ExecuteRequest, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.certify_reconciliation(sid, b.idempotency_key)
    except Exception as e:
        raise err(e) from e


@router.post("/statements")
async def statements(b: StatementRequest, s: Annotated[CompletionService, Depends(svc)]):
    return await s.statement(b.ledger_id, b.period_id)

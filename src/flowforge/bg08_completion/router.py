from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .schemas import *  # noqa: F403, F405
from .service import CompletionService

router = APIRouter(prefix="/api/v2/bg08/completion", tags=["bg08-completion"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D) -> Any:
    return CompletionService(db, TenantContext(p.tenant_id, p.user_id))


def fail(e) -> Any:
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/subscriptions/{id}/amend")
async def amend(id: UUID, b: AmendmentCreate, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.amend(id, b)
    except (LookupError, ValueError) as e:
        raise fail(e) from e


@router.post("/subscriptions/{id}/entitlements/{code}/consume")
async def consume(
    id: UUID, code: str, quantity: Decimal, s: Annotated[CompletionService, Depends(svc)]
):
    try:
        return await s.enforce(id, code, quantity)
    except (LookupError, ValueError) as e:
        raise fail(e) from e


@router.post("/billing-runs/{id}/execute")
async def execute(id: UUID, b: Idem, s: Annotated[CompletionService, Depends(svc)]):
    return await s.execute_billing(id, b.idempotency_key)


@router.post("/projects/bill")
async def project_bill(b: ProjectBillingCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.project_bill(b)


@router.post("/asset-transactions/{id}/post")
async def asset_post(id: UUID, b: AssetAccounting, s: Annotated[CompletionService, Depends(svc)]):
    return await s.asset_post(id, b)

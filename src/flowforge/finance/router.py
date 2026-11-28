from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .service import FinanceService

router = APIRouter(prefix="/api/v2/finance", tags=["finance"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D) -> FinanceService:
    return FinanceService(db, TenantContext(p.tenant_id, p.user_id))


@router.get("/dashboard")
async def dashboard(s: Annotated[FinanceService, Depends(svc)], as_of: date | None = None):
    return await s.dashboard(as_of or date.today())


@router.get("/controls/journal-integrity")
async def journal_integrity(s: Annotated[FinanceService, Depends(svc)]):
    return await s.journal_integrity()


@router.get("/controls/subledger-integrity")
async def subledger_integrity(s: Annotated[FinanceService, Depends(svc)]):
    return await s.subledger_integrity()


@router.get("/close/readiness")
async def close_readiness(s: Annotated[FinanceService, Depends(svc)]):
    return await s.period_readiness()

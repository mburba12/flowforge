from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .posting import PostingEngine
from .schemas import (
    AccountCreate,
    CalendarCreate,
    CurrencyCreate,
    JournalCreate,
    LedgerCreate,
    PeriodCreate,
)
from .service import LedgerService

router = APIRouter(prefix="/api/v2", tags=["phase2b"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(principal: P, db: D) -> LedgerService:
    return LedgerService(db, principal.tenant_id, principal.user_id)


@router.post("/currencies", status_code=201)
async def create_currency(
    body: CurrencyCreate, svc: Annotated[LedgerService, Depends(service)]
) -> dict[str, str]:
    item = await svc.currency(body)
    return {"code": item.code, "name": item.name}


@router.post("/fiscal-calendars", status_code=201)
async def create_calendar(
    body: CalendarCreate, svc: Annotated[LedgerService, Depends(service)]
) -> dict[str, str]:
    item = await svc.calendar(body)
    return {"id": str(item.id), "name": item.name}


@router.post("/accounting-periods", status_code=201)
async def create_period(
    body: PeriodCreate, svc: Annotated[LedgerService, Depends(service)]
) -> dict[str, str]:
    item = await svc.period(body)
    return {"id": str(item.id), "status": item.status}


@router.post("/ledgers", status_code=201)
async def create_ledger(
    body: LedgerCreate, svc: Annotated[LedgerService, Depends(service)]
) -> dict[str, str]:
    item = await svc.ledger(body)
    return {"id": str(item.id), "code": item.code}


@router.post("/accounts", status_code=201)
async def create_account(
    body: AccountCreate, svc: Annotated[LedgerService, Depends(service)]
) -> dict[str, str]:
    item = await svc.account(body)
    return {"id": str(item.id), "account_code": item.account_code}


@router.post("/journals", status_code=201)
async def create_journal(
    body: JournalCreate, svc: Annotated[LedgerService, Depends(service)]
) -> dict[str, str]:
    item = await svc.journal(body)
    return {"id": str(item.id), "journal_number": item.journal_number, "status": item.status}


@router.post("/journals/{journal_id}/approve")
async def approve_journal(journal_id: UUID, principal: P, db: D) -> dict[str, str]:
    from sqlalchemy import select

    from .models import JournalEntry

    item = await db.scalar(
        select(JournalEntry).where(
            JournalEntry.id == journal_id, JournalEntry.tenant_id == principal.tenant_id
        )
    )
    if item is None:
        from fastapi import HTTPException

        raise HTTPException(404, "Journal not found")
    if item.created_by == principal.user_id:
        from fastapi import HTTPException

        raise HTTPException(409, "Journal creator cannot approve the same journal")
    item.status = "approved"
    item.approved_by = principal.user_id
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.post("/journals/{journal_id}/post")
async def post_journal(journal_id: UUID, principal: P, db: D) -> dict[str, str]:
    item = await PostingEngine(db, principal.tenant_id, principal.user_id).post(journal_id)
    return {"id": str(item.id), "status": item.status}


@router.get("/trial-balance")
async def trial_balance(
    ledger_id: UUID, period_id: UUID, svc: Annotated[LedgerService, Depends(service)]
) -> dict[str, str]:
    result = await svc.trial_balance(ledger_id, period_id)
    return {"debit": str(result["debit"]), "credit": str(result["credit"])}

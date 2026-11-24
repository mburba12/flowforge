from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_db

from .schemas import PayrollCalculate, PayrollPaymentCreate, PayrollPostAccounts, PayrollRunCreate
from .service import PayrollError, PayrollService

router = APIRouter(prefix="/api/v4a/payroll", tags=["phase4a-payroll"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_db)]


def service(principal: P, db: D) -> PayrollService:
    return PayrollService(db, principal.tenant_id, principal.user_id)


S = Annotated[PayrollService, Depends(service)]


@router.post("/runs", status_code=201)
async def create_run(body: PayrollRunCreate, svc: S) -> dict[str, str]:
    item = await svc.create_run(body)
    return {"id": str(item.id), "run_number": item.run_number, "status": item.status}


@router.post("/runs/{run_id}/calculate")
async def calculate(run_id: UUID, body: PayrollCalculate, svc: S) -> dict[str, str]:
    try:
        item = await svc.calculate(run_id, body)
    except (PayrollError, ValueError) as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"id": str(item.id), "status": item.status}


@router.post("/runs/{run_id}/approve")
async def approve(run_id: UUID, svc: S) -> dict[str, str]:
    try:
        item = await svc.approve(run_id)
    except PayrollError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"id": str(item.id), "status": item.status}


@router.post("/runs/{run_id}/post")
async def post(run_id: UUID, body: PayrollPostAccounts, svc: S) -> dict[str, str]:
    try:
        item = await svc.post(run_id, body)
    except PayrollError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"id": str(item.id), "status": item.status, "journal_id": str(item.posted_journal_id)}


@router.post("/runs/{run_id}/payments", status_code=201)
async def payment(run_id: UUID, body: PayrollPaymentCreate, svc: S) -> dict[str, str]:
    try:
        item = await svc.pay_worker(run_id, body)
    except PayrollError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"id": str(item.id), "status": item.status, "amount": str(item.amount)}


@router.post("/runs/{run_id}/reconcile")
async def reconcile(run_id: UUID, svc: S) -> dict[str, str]:
    try:
        item = await svc.reconcile(run_id)
    except PayrollError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {
        "id": str(item.id),
        "status": item.status,
        "subledger_total": str(item.subledger_total),
        "gl_total": str(item.gl_total),
    }

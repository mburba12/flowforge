from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .schemas import (
    AssignmentCreate,
    BankAccountCreate,
    BenefitEnrollmentCreate,
    BenefitPlanCreate,
    CompensationCreate,
    TaxProfileCreate,
    WorkerCreate,
    WorkLocationCreate,
)
from .service import WorkforceError, WorkforceService

router = APIRouter(prefix="/api/v4a", tags=["phase4a"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(principal: P, db: D) -> WorkforceService:
    return WorkforceService(db, principal.tenant_id, principal.user_id)


S = Annotated[WorkforceService, Depends(service)]


@router.post("/workers", status_code=201)
async def create_worker(body: WorkerCreate, svc: S) -> dict[str, str]:
    item = await svc.create_worker(body)
    return {
        "id": str(item.id),
        "worker_number": item.worker_number,
        "status": item.employment_status,
    }


@router.post("/work-locations", status_code=201)
async def create_location(body: WorkLocationCreate, svc: S) -> dict[str, str]:
    item = await svc.create_location(body)
    return {"id": str(item.id), "code": item.code}


@router.post("/workers/{worker_id}/assignments", status_code=201)
async def assign(worker_id: UUID, body: AssignmentCreate, svc: S) -> dict[str, str]:
    try:
        item = await svc.assign(worker_id, body)
    except WorkforceError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"id": str(item.id)}


@router.post("/workers/{worker_id}/compensation", status_code=201)
async def compensation(worker_id: UUID, body: CompensationCreate, svc: S) -> dict[str, str]:
    try:
        item = await svc.compensation(worker_id, body)
    except WorkforceError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"id": str(item.id), "amount": str(item.amount)}


@router.post("/workers/{worker_id}/bank-accounts", status_code=201)
async def bank_account(worker_id: UUID, body: BankAccountCreate, svc: S) -> dict[str, str]:
    item = await svc.bank_account(worker_id, body)
    return {
        "id": str(item.id),
        "account_last4": item.account_last4,
        "account_type": item.account_type,
    }


@router.post("/workers/{worker_id}/tax-profiles", status_code=201)
async def tax_profile(worker_id: UUID, body: TaxProfileCreate, svc: S) -> dict[str, str]:
    item = await svc.tax_profile(worker_id, body)
    return {"id": str(item.id), "filing_status": item.filing_status}


@router.post("/benefit-plans", status_code=201)
async def benefit_plan(body: BenefitPlanCreate, svc: S) -> dict[str, str]:
    item = await svc.benefit_plan(body)
    return {"id": str(item.id), "code": item.code}


@router.post("/workers/{worker_id}/benefit-enrollments", status_code=201)
async def enroll(worker_id: UUID, body: BenefitEnrollmentCreate, svc: S) -> dict[str, str]:
    item = await svc.enroll(worker_id, body)
    return {"id": str(item.id)}

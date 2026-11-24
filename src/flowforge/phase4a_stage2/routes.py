from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_db

from .schemas import (
    LeaveRequestCreate,
    LeaveTypeCreate,
    PayGroupCreate,
    PayPeriodCreate,
    ScheduleCreate,
    TimeEntryCreate,
)
from .service import TimeLeaveError, TimeLeaveService

router = APIRouter(prefix="/api/v4a", tags=["phase4a-time"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_db)]


def service(principal: P, db: D) -> TimeLeaveService:
    return TimeLeaveService(db, principal.tenant_id, principal.user_id)


S = Annotated[TimeLeaveService, Depends(service)]


@router.post("/work-schedules", status_code=201)
async def schedule(body: ScheduleCreate, svc: S) -> dict[str, str]:
    item = await svc.schedule(body)
    return {"id": str(item.id), "code": item.code}


@router.post("/time-entries", status_code=201)
async def time_entry(body: TimeEntryCreate, svc: S) -> dict[str, str]:
    try:
        item = await svc.time_entry(body)
    except TimeLeaveError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"id": str(item.id), "status": item.status}


@router.post("/time-entries/{entry_id}/approve")
async def approve_time(entry_id: UUID, svc: S) -> dict[str, str]:
    try:
        item = await svc.approve_time(entry_id)
    except TimeLeaveError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"id": str(item.id), "status": item.status}


@router.post("/leave-types", status_code=201)
async def leave_type(body: LeaveTypeCreate, svc: S) -> dict[str, str]:
    item = await svc.leave_type(body)
    return {"id": str(item.id), "code": item.code}


@router.post("/leave-requests", status_code=201)
async def leave_request(body: LeaveRequestCreate, svc: S) -> dict[str, str]:
    item = await svc.leave_request(body)
    return {"id": str(item.id), "status": item.status}


@router.post("/pay-groups", status_code=201)
async def pay_group(body: PayGroupCreate, svc: S) -> dict[str, str]:
    item = await svc.pay_group(body)
    return {"id": str(item.id), "code": item.code}


@router.post("/pay-periods", status_code=201)
async def pay_period(body: PayPeriodCreate, svc: S) -> dict[str, str]:
    item = await svc.pay_period(body)
    return {"id": str(item.id), "status": item.status}

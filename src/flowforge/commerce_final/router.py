from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405
from .service import CommerceService

router = APIRouter(prefix="/api/v2/commerce/final", tags=["commerce-final"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D) -> Any:
    return CommerceService(db, TenantContext(p.tenant_id, p.user_id))


def fail(e) -> Any:
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/requisitions", status_code=201)
async def req(b: RequisitionCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.requisition(b)


@router.post("/requisitions/{id}/action")
async def req_action(id: UUID, b: Action, s: Annotated[CommerceService, Depends(svc)]):
    try:
        return await s.requisition_action(id, b.target)
    except Exception as e:
        raise fail(e) from e


@router.post("/transfers", status_code=201)
async def transfer(b: TransferCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.transfer(b)


@router.post("/transfers/{id}/action")
async def transfer_action(id: UUID, b: Action, s: Annotated[CommerceService, Depends(svc)]):
    try:
        return await s.transfer_action(id, b.target, b.idempotency_key)
    except Exception as e:
        raise fail(e) from e


@router.post("/counts", status_code=201)
async def count(b: CountCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.count(b)


@router.post("/counts/{id}/lines", status_code=201)
async def count_line(id: UUID, b: CountLineCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.count_line(id, b)


@router.post("/returns", status_code=201)
async def ret(b: ReturnCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.return_create(b)


@router.post("/returns/{id}/action")
async def return_action(id: UUID, b: Action, s: Annotated[CommerceService, Depends(svc)]):
    try:
        return await s.return_action(id, b.target)
    except Exception as e:
        raise fail(e) from e


@router.post("/shipping/rates", status_code=201)
async def rate(b: RateCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.save(ShippingRate(tenant_id=s.ctx.tenant_id, **b.model_dump()), "shipping_rate")


@router.post("/shipping/labels", status_code=201)
async def label(b: LabelCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.label(b)


@router.post("/shipping/tracking-events", status_code=201)
async def tracking(b: TrackingCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.save(
        TrackingEvent(tenant_id=s.ctx.tenant_id, **b.model_dump()), "tracking_event"
    )


@router.post("/shipping/claims", status_code=201)
async def claim(b: ClaimCreate, s: Annotated[CommerceService, Depends(svc)]):
    return await s.claim(b)


@router.get("/inventory/lots")
async def lots(s: Annotated[CommerceService, Depends(svc)]):
    return await s.list(InventoryLot)


@router.get("/inventory/serials")
async def serials(s: Annotated[CommerceService, Depends(svc)]):
    return await s.list(InventorySerial)

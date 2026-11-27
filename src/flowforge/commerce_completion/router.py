from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import LandedCost, Manifest
from .schemas import *  # noqa: F403, F405
from .service import CompletionService

router = APIRouter(prefix="/api/v2/commerce/completion", tags=["commerce-completion"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D):
    return CompletionService(db, TenantContext(p.tenant_id, p.user_id))


def fail(e):
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/requisitions/{id}/convert-po")
async def convert(id: UUID, b: ConvertPO, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.requisition_to_po(id, b)
    except Exception as e:
        raise fail(e) from e


@router.post("/reservations")
async def reserve(b: Reserve, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.reserve(b)
    except Exception as e:
        raise fail(e) from e


@router.post("/counts/{id}/approve")
async def count(id: UUID, b: Idem, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.approve_count(id, b.idempotency_key)
    except Exception as e:
        raise fail(e) from e


@router.post("/fulfill")
async def fulfill(b: Fulfill, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.fulfill(b)
    except Exception as e:
        raise fail(e) from e


@router.post("/returns/{id}/receive")
async def receive(id: UUID, b: ReturnReceive, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.receive_return(id, b)
    except Exception as e:
        raise fail(e) from e


@router.post("/landed-costs", status_code=201)
async def landed(b: LandedCostCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.save(LandedCost(tenant_id=s.ctx.tenant_id, **b.model_dump()), "landed_cost")


@router.post("/manifests", status_code=201)
async def manifest(b: ManifestCreate, s: Annotated[CompletionService, Depends(svc)]):
    return await s.save(
        Manifest(
            tenant_id=s.ctx.tenant_id,
            shipment_ids_json=__import__("json").dumps([str(x) for x in b.shipment_ids]),
            manifest_number=b.manifest_number,
            carrier_code=b.carrier_code,
        ),
        "manifest",
    )


@router.post("/claims/{id}/action")
async def claim(id: UUID, b: ClaimAction, s: Annotated[CompletionService, Depends(svc)]):
    try:
        return await s.claim_action(id, b.target)
    except Exception as e:
        raise fail(e) from e


@router.get("/inventory/valuation")
async def valuation(s: Annotated[CompletionService, Depends(svc)]):
    return await s.valuation()

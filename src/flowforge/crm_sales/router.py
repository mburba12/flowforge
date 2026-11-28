from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405
from .service import CRMService

router = APIRouter(prefix="/api/v2/crm", tags=["crm-sales"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D) -> Any:
    return CRMService(db, TenantContext(p.tenant_id, p.user_id))


def err(e) -> Any:
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/leads", status_code=201)
async def lead(b: LeadCreate, s: Annotated[CRMService, Depends(svc)]):
    return await s.lead(b)


@router.post("/leads/{id}/convert")
async def convert(id: UUID, s: Annotated[CRMService, Depends(svc)]):
    try:
        return await s.convert_lead(id)
    except (LookupError, ValueError) as e:
        raise err(e) from e


@router.post("/opportunities", status_code=201)
async def opp(b: OpportunityCreate, s: Annotated[CRMService, Depends(svc)]):
    return await s.opportunity(b)


@router.post("/activities", status_code=201)
async def activity(b: ActivityCreate, s: Annotated[CRMService, Depends(svc)]):
    return await s.save(Activity(tenant_id=s.ctx.tenant_id, **b.model_dump()), "crm_activity")


@router.post("/campaigns", status_code=201)
async def campaign(b: CampaignCreate, s: Annotated[CRMService, Depends(svc)]):
    return await s.save(Campaign(tenant_id=s.ctx.tenant_id, **b.model_dump()), "crm_campaign")


@router.post("/quotes", status_code=201)
async def quote(b: QuoteCreate, s: Annotated[CRMService, Depends(svc)]):
    return await s.quote(b)


@router.post("/quotes/{id}/transition")
async def quote_transition(id: UUID, b: Transition, s: Annotated[CRMService, Depends(svc)]):
    try:
        return await s.transition_quote(id, b.target, b.reason)
    except (LookupError, ValueError) as e:
        raise err(e) from e


@router.post("/credit-profiles", status_code=201)
async def credit(b: CreditCreate, s: Annotated[CRMService, Depends(svc)]):
    return await s.save(
        CreditProfile(tenant_id=s.ctx.tenant_id, **b.model_dump()), "credit_profile"
    )


@router.get("/credit-check/{party_id}")
async def check(party_id: UUID, amount: Decimal, s: Annotated[CRMService, Depends(svc)]):
    return await s.credit_check(party_id, amount)


@router.post("/communications", status_code=201)
async def comm(b: CommunicationCreate, s: Annotated[CRMService, Depends(svc)]):
    return await s.save(
        Communication(tenant_id=s.ctx.tenant_id, **b.model_dump()), "crm_communication"
    )


@router.get("/dashboard")
async def dashboard(s: Annotated[CRMService, Depends(svc)]):
    return await s.dashboard()


@router.get("/portal/parties/{party_id}/orders")
async def orders(party_id: UUID, s: Annotated[CRMService, Depends(svc)]):
    return await s.order_status(party_id)

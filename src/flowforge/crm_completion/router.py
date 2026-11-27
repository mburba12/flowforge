from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.crm_sales.models import Lead, Opportunity, Quote
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405
from .service import CRMCompletionService

router = APIRouter(prefix="/api/v2/crm/completion", tags=["crm-completion"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D):
    return CRMCompletionService(db, TenantContext(p.tenant_id, p.user_id))


def fail(e):
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/price-lists", status_code=201)
async def price_list(b: PriceListCreate, s: Annotated[CRMCompletionService, Depends(svc)]):
    return await s.save(PriceList(tenant_id=s.ctx.tenant_id, **b.model_dump()), "price_list")


@router.post("/price-lists/{id}/items", status_code=201)
async def price_item(
    id: UUID, b: PriceItemCreate, s: Annotated[CRMCompletionService, Depends(svc)]
):
    return await s.save(
        PriceListItem(tenant_id=s.ctx.tenant_id, price_list_id=id, **b.model_dump()),
        "price_list_item",
    )


@router.post("/pricing/calculate")
async def pricing(b: PriceRequest, s: Annotated[CRMCompletionService, Depends(svc)]):
    try:
        return await s.price(b)
    except Exception as e:
        raise fail(e) from e


@router.post("/campaigns/{id}/members", status_code=201)
async def member(
    id: UUID, b: CampaignMemberCreate, s: Annotated[CRMCompletionService, Depends(svc)]
):
    if bool(b.party_id) == bool(b.lead_id):
        raise HTTPException(422, "Exactly one member reference required")
    return await s.save(
        CampaignMember(tenant_id=s.ctx.tenant_id, campaign_id=id, **b.model_dump()),
        "campaign_member",
    )


@router.post("/quotes/{id}/revise")
async def revise(id: UUID, b: QuoteRevise, s: Annotated[CRMCompletionService, Depends(svc)]):
    try:
        return await s.revise_quote(id, b.reason, b.idempotency_key)
    except Exception as e:
        raise fail(e) from e


@router.post("/credit/{party_id}/recompute")
async def credit(party_id: UUID, s: Annotated[CRMCompletionService, Depends(svc)]):
    try:
        return await s.recompute_credit(party_id)
    except Exception as e:
        raise fail(e) from e


@router.post("/portal/users", status_code=201)
async def portal_user(b: PortalUserCreate, s: Annotated[CRMCompletionService, Depends(svc)]):
    return await s.save(PortalUser(tenant_id=s.ctx.tenant_id, **b.model_dump()), "portal_user")


@router.post("/search/leads")
async def leads(b: SearchRequest, s: Annotated[CRMCompletionService, Depends(svc)]):
    return await s.search(Lead, b, ["lead_number", "company_name", "contact_name", "email"])


@router.post("/search/opportunities")
async def opportunities(b: SearchRequest, s: Annotated[CRMCompletionService, Depends(svc)]):
    return await s.search(Opportunity, b, ["opportunity_number", "name", "stage"])


@router.post("/search/quotes")
async def quotes(b: SearchRequest, s: Annotated[CRMCompletionService, Depends(svc)]):
    return await s.search(Quote, b, ["quote_number", "status", "currency_code"])


@router.get("/reports/funnel")
async def funnel(s: Annotated[CRMCompletionService, Depends(svc)]):
    return await s.funnel()

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,Header,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.core.security import Principal,current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext
from flowforge.crm_sales.models import Activity,Campaign,Communication,Lead,Opportunity,Quote
from .schemas import *
from .service import CRMFinalService
router=APIRouter(prefix='/api/v2/crm/final',tags=['crm-final'])
P=Annotated[Principal,Depends(current_principal)];D=Annotated[AsyncSession,Depends(get_tenant_db)]
def svc(p:P,db:D):return CRMFinalService(db,TenantContext(p.tenant_id,p.user_id))
def x(e):return HTTPException(404 if isinstance(e,LookupError) else 409,str(e))
@router.get('/leads')
async def leads(s:Annotated[CRMFinalService,Depends(svc)]):return await s.list(Lead)
@router.get('/opportunities')
async def opportunities(s:Annotated[CRMFinalService,Depends(svc)]):return await s.list(Opportunity)
@router.post('/opportunities/{id}/transition')
async def opp(id:UUID,b:OpportunityTransition,s:Annotated[CRMFinalService,Depends(svc)]):
 try:return await s.opportunity(id,b)
 except Exception as e:raise x(e) from e
@router.post('/activities/{id}/complete')
async def activity(id:UUID,s:Annotated[CRMFinalService,Depends(svc)]):return await s.complete_activity(id)
@router.post('/campaigns/{id}/transition')
async def campaign(id:UUID,b:CampaignTransition,s:Annotated[CRMFinalService,Depends(svc)]):
 try:return await s.campaign(id,b.status)
 except Exception as e:raise x(e) from e
@router.get('/quotes')
async def quotes(s:Annotated[CRMFinalService,Depends(svc)]):return await s.list(Quote)
@router.post('/quotes/{id}/convert-order')
async def convert(id:UUID,b:QuoteConvert,s:Annotated[CRMFinalService,Depends(svc)]):
 try:return await s.quote_to_order(id,b)
 except Exception as e:raise x(e) from e
@router.post('/credit/{party_id}/exposure')
async def exposure(party_id:UUID,b:CreditExposure,s:Annotated[CRMFinalService,Depends(svc)]):
 try:return await s.exposure(party_id,b.delta,b.reason)
 except Exception as e:raise x(e) from e
@router.get('/communications/{party_id}')
async def communications(party_id:UUID,s:Annotated[CRMFinalService,Depends(svc)]):
 return list((await s.db.scalars(__import__('sqlalchemy').select(Communication).where(Communication.tenant_id==s.ctx.tenant_id,Communication.party_id==party_id).order_by(Communication.created_at.desc()))).all())
@router.post('/portal/tokens')
async def token(b:PortalIssue,s:Annotated[CRMFinalService,Depends(svc)]):return await s.issue_portal(b.party_id,b.expires_in_minutes)
@router.get('/portal/validate')
async def validate(s:Annotated[CRMFinalService,Depends(svc)],x_portal_token:Annotated[str,Header()]):
 try:return await s.validate_portal(x_portal_token)
 except PermissionError as e:raise HTTPException(401,str(e)) from e

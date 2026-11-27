import json
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.core.security import Principal,current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext
from .models import *
from .schemas import *
from .service import FoundationService
router=APIRouter(prefix='/api/v2/foundation-completion',tags=['foundation-completion'])
P=Annotated[Principal,Depends(current_principal)];D=Annotated[AsyncSession,Depends(get_tenant_db)]
def svc(p:P,db:D):return FoundationService(db,TenantContext(p.tenant_id,p.user_id))
@router.post('/entitlements',status_code=201)
async def entitlement(b:EntitlementCreate,s:Annotated[FoundationService,Depends(svc)]):return await s.entitlement(b.module_code,b.dependencies)
@router.post('/entitlements/{eid}/disable')
async def disable(eid:UUID,s:Annotated[FoundationService,Depends(svc)]):
 try:return await s.disable(eid)
 except Exception as e:raise HTTPException(409,str(e)) from e
@router.post('/access-reviews',status_code=201)
async def review(b:AccessReviewCreate,s:Annotated[FoundationService,Depends(svc)]):return await s.save(AccessReview(tenant_id=s.ctx.tenant_id,name=b.name,reviewer_id=b.reviewer_id,scope_json=json.dumps(b.scope)),'access_review')
@router.post('/support-grants',status_code=201)
async def support(b:SupportGrantCreate,s:Annotated[FoundationService,Depends(svc)]):
 try:return await s.support(b)
 except ValueError as e:raise HTTPException(422,str(e)) from e
@router.post('/stewardship',status_code=201)
async def stewardship(b:StewardshipCreate,s:Annotated[FoundationService,Depends(svc)]):return await s.save(StewardshipTask(tenant_id=s.ctx.tenant_id,party_id=b.party_id,task_type=b.task_type,assigned_to=b.assigned_to,priority=b.priority,details_json=json.dumps(b.details)),'stewardship_task')
@router.post('/quality-rules',status_code=201)
async def quality(b:QualityRuleCreate,s:Annotated[FoundationService,Depends(svc)]):return await s.save(DataQualityRule(tenant_id=s.ctx.tenant_id,code=b.code,entity_type=b.entity_type,rule_type=b.rule_type,configuration_json=json.dumps(b.configuration)),'data_quality_rule')
@router.post('/exports',status_code=201)
async def export(b:ExportCreate,s:Annotated[FoundationService,Depends(svc)]):return await s.save(ExportJob(tenant_id=s.ctx.tenant_id,job_type=b.job_type,format=b.format,cursor=b.cursor,requested_by=s.ctx.user_id),'export_job')
@router.get('/stewardship')
async def tasks(s:Annotated[FoundationService,Depends(svc)]):return await s.list(StewardshipTask)

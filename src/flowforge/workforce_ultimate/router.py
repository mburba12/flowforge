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
from .service import UltimateService
router=APIRouter(prefix='/api/v2/workforce/ultimate',tags=['workforce-ultimate'])
P=Annotated[Principal,Depends(current_principal)];D=Annotated[AsyncSession,Depends(get_tenant_db)]
def svc(p:P,db:D):return UltimateService(db,TenantContext(p.tenant_id,p.user_id))
@router.post('/interviews',status_code=201)
async def interview(b:InterviewCreate,s:Annotated[UltimateService,Depends(svc)]):return await s.save(Interview(tenant_id=s.ctx.tenant_id,application_id=b.application_id,scheduled_at=b.scheduled_at,panel_json=json.dumps([str(x) for x in b.panel_ids])),'interview')
@router.post('/interviews/{id}/feedback')
async def feedback(id:UUID,b:InterviewFeedback,s:Annotated[UltimateService,Depends(svc)]):
 x=await s.db.scalar(__import__('sqlalchemy').select(Interview).where(Interview.id==id,Interview.tenant_id==s.ctx.tenant_id));
 if not x:raise HTTPException(404,'Interview not found')
 x.scorecard_json=json.dumps({'scores':b.scores,'notes':b.notes});x.status='completed';await s.db.commit();return x
@router.post('/onboarding-templates',status_code=201)
async def onboarding(b:TemplateCreate,s:Annotated[UltimateService,Depends(svc)]):return await s.save(OnboardingTemplate(tenant_id=s.ctx.tenant_id,code=b.code,name=b.name,tasks_json=json.dumps(b.items)),'onboarding_template')
@router.post('/review-templates',status_code=201)
async def review_template(b:TemplateCreate,s:Annotated[UltimateService,Depends(svc)]):return await s.save(ReviewTemplate(tenant_id=s.ctx.tenant_id,code=b.code,name=b.name,competencies_json=json.dumps(b.items)),'review_template')
@router.post('/benefit-dependents',status_code=201)
async def dependent(b:DependentCreate,s:Annotated[UltimateService,Depends(svc)]):return await s.dependent(b)
@router.post('/clock-events',status_code=201)
async def clock(b:ClockCreate,s:Annotated[UltimateService,Depends(svc)]):return await s.save(TimeClockEvent(tenant_id=s.ctx.tenant_id,**b.model_dump()),'clock_event')
@router.post('/payroll-transfers',status_code=201)
async def transfer(b:TransferCreate,s:Annotated[UltimateService,Depends(svc)]):return await s.save(PayrollTransfer(tenant_id=s.ctx.tenant_id,worker_id=b.worker_id,source_type=b.source_type,source_id=b.source_id,idempotency_key=b.idempotency_key,payload_json=json.dumps(b.payload)),'payroll_transfer')
@router.post('/reports')
async def reports(b:ReportRequest,s:Annotated[UltimateService,Depends(svc)]):
 try:return await s.report(b.report_code,b.parameters)
 except ValueError as e:raise HTTPException(422,str(e)) from e

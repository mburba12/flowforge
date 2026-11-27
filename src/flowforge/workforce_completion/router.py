from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.core.security import Principal,current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext
from .models import *
from .schemas import *
from .service import CompletionService
router=APIRouter(prefix='/api/v2/workforce/completion',tags=['workforce-completion'])
P=Annotated[Principal,Depends(current_principal)];D=Annotated[AsyncSession,Depends(get_tenant_db)]
def svc(p:P,db:D):return CompletionService(db,TenantContext(p.tenant_id,p.user_id))
def fail(e):return HTTPException(404 if isinstance(e,LookupError) else 409,str(e))
@router.post('/assignments',status_code=201)
async def assignment(b:AssignmentCreate,s:Annotated[CompletionService,Depends(svc)]):
 try:return await s.assignment(b)
 except Exception as e:raise fail(e) from e
@router.post('/compensation',status_code=201)
async def compensation(b:CompensationCreate,s:Annotated[CompletionService,Depends(svc)]):
 try:return await s.compensation(b)
 except Exception as e:raise fail(e) from e
@router.post('/schedules',status_code=201)
async def schedule(b:ScheduleCreate,s:Annotated[CompletionService,Depends(svc)]):
 if b.end_time<=b.start_time:raise HTTPException(422,'End time must follow start time')
 return await s.save(Schedule(tenant_id=s.ctx.tenant_id,**b.model_dump()),'worker_schedule')
@router.post('/timecards',status_code=201)
async def timecard(b:TimecardCreate,s:Annotated[CompletionService,Depends(svc)]):return await s.save(Timecard(tenant_id=s.ctx.tenant_id,**b.model_dump()),'timecard')
@router.post('/timecards/{id}/action')
async def time_action(id:UUID,b:Action,s:Annotated[CompletionService,Depends(svc)]):
 try:return await s.action(Timecard,id,b.target,b.idempotency_key,{'draft':{'submitted'},'submitted':{'approved','rejected'},'rejected':{'draft'}})
 except Exception as e:raise fail(e) from e
@router.post('/leave-policies',status_code=201)
async def policy(b:LeavePolicyCreate,s:Annotated[CompletionService,Depends(svc)]):return await s.save(LeavePolicy(tenant_id=s.ctx.tenant_id,**b.model_dump()),'leave_policy')
@router.post('/leave',status_code=201)
async def leave(b:LeaveCreate,s:Annotated[CompletionService,Depends(svc)]):
 if b.ends_on<b.starts_on:raise HTTPException(422,'Invalid leave dates')
 balance=await s.leave_balance(b.worker_id,b.policy_id)
 if b.units>balance['available']:raise HTTPException(409,'Insufficient leave balance')
 return await s.save(LeaveRequest(tenant_id=s.ctx.tenant_id,**b.model_dump()),'leave_request')
@router.post('/leave/{id}/action')
async def leave_action(id:UUID,b:Action,s:Annotated[CompletionService,Depends(svc)]):return await s.action(LeaveRequest,id,b.target,b.idempotency_key,{'draft':{'submitted','cancelled'},'submitted':{'approved','rejected'},'approved':{'cancelled'}})
@router.get('/leave/balance/{worker_id}/{policy_id}')
async def balance(worker_id:UUID,policy_id:UUID,s:Annotated[CompletionService,Depends(svc)]):return await s.leave_balance(worker_id,policy_id)
@router.post('/lifecycle-tasks',status_code=201)
async def task(b:LifecycleTaskCreate,s:Annotated[CompletionService,Depends(svc)]):return await s.save(LifecycleTask(tenant_id=s.ctx.tenant_id,**b.model_dump()),'lifecycle_task')
@router.post('/lifecycle-tasks/{id}/action')
async def task_action(id:UUID,b:Action,s:Annotated[CompletionService,Depends(svc)]):return await s.action(LifecycleTask,id,b.target,b.idempotency_key,{'open':{'in_progress','cancelled'},'in_progress':{'completed','blocked'},'blocked':{'in_progress','cancelled'}})
@router.post('/retirement-plans',status_code=201)
async def retirement_plan(b:RetirementPlanCreate,s:Annotated[CompletionService,Depends(svc)]):return await s.save(RetirementPlan(tenant_id=s.ctx.tenant_id,**b.model_dump()),'retirement_plan')
@router.post('/retirement-enrollments',status_code=201)
async def retirement_enroll(b:RetirementEnroll,s:Annotated[CompletionService,Depends(svc)]):
 p=await s.get(RetirementPlan,b.plan_id)
 if b.employee_bps>p.employee_max_bps:raise HTTPException(422,'Contribution exceeds plan maximum')
 return await s.save(RetirementEnrollment(tenant_id=s.ctx.tenant_id,**b.model_dump()),'retirement_enrollment')
@router.post('/documents',status_code=201)
async def document(b:DocumentCreate,s:Annotated[CompletionService,Depends(svc)]):return await s.save(WorkerDocument(tenant_id=s.ctx.tenant_id,**b.model_dump()),'worker_document')
@router.get('/documents/{id}/access')
async def document_access(id:UUID,s:Annotated[CompletionService,Depends(svc)]):return await s.document_access(id)

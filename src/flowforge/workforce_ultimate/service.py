from __future__ import annotations
import hashlib,json
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change
from flowforge.workforce_final.models import Application,Candidate,Enrollment,Goal,PerformanceReview,Position
from flowforge.workforce_completion.models import Assignment,Compensation,LeaveRequest,LifecycleTask,Timecard
from .models import *
class UltimateService:
 def __init__(self,db:AsyncSession,ctx:TenantContext):self.db=db;self.ctx=ctx
 async def save(self,o,e):self.db.add(o);await self.db.flush();await record_change(self.db,self.ctx.tenant_id,self.ctx.user_id,'created',e,str(o.id));await self.db.commit();await self.db.refresh(o);return o
 async def report(self,code,params):
  models={'headcount':Assignment,'recruiting_funnel':Application,'performance':PerformanceReview,'training':Enrollment,'leave':LeaveRequest}
  if code not in models:raise ValueError('Unsupported report')
  count=int((await self.db.scalar(select(func.count()).select_from(models[code]).where(models[code].tenant_id==self.ctx.tenant_id))) or 0)
  return await self.save(WorkforceReportRun(tenant_id=self.ctx.tenant_id,report_code=code,parameters_json=json.dumps(params),result_json=json.dumps({'count':count}),requested_by=self.ctx.user_id),'workforce_report')
 async def dependent(self,b):
  encrypted=hashlib.sha256(b.identifier.encode()).hexdigest() if b.identifier else None
  return await self.save(BenefitDependent(tenant_id=self.ctx.tenant_id,worker_id=b.worker_id,name=b.name,relationship=b.relationship,encrypted_identifier=encrypted),'benefit_dependent')

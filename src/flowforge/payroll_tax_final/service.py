from __future__ import annotations
import json
from decimal import Decimal
from uuid import UUID
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change
from flowforge.phase4a_stage3.models import PayrollRun,PayrollRunWorker,PayrollLiability,PayrollPayment
from flowforge.phase4b_stage2.models import TaxLiability,TaxNotice,TaxReturn,TaxRemittance
from .models import *
class PayrollTaxService:
 def __init__(self,db:AsyncSession,ctx:TenantContext):self.db=db;self.ctx=ctx
 async def save(self,o,e):self.db.add(o);await self.db.flush();await record_change(self.db,self.ctx.tenant_id,self.ctx.user_id,'created',e,str(o.id));await self.db.commit();await self.db.refresh(o);return o
 async def get(self,m,id):
  x=await self.db.scalar(select(m).where(m.id==id,m.tenant_id==self.ctx.tenant_id));
  if not x:raise LookupError('Record not found')
  return x
 async def adjustment_action(self,id,target,key):
  a=await self.get(PayrollAdjustment,id);old=await self.db.scalar(select(PayrollExecution).where(PayrollExecution.tenant_id==self.ctx.tenant_id,PayrollExecution.operation==target,PayrollExecution.idempotency_key==key))
  if old:return old
  allowed={'draft':{'submitted','cancelled'},'submitted':{'approved','rejected'},'approved':{'applied','reversed'}}
  if target not in allowed.get(a.status,set()):raise ValueError('Invalid adjustment transition')
  if target=='approved':a.approved_by=self.ctx.user_id
  a.status=target;e=PayrollExecution(tenant_id=self.ctx.tenant_id,operation=target,idempotency_key=key,aggregate_type='adjustment',aggregate_id=a.id,actor_user_id=self.ctx.user_id);self.db.add(e);await self.db.commit();return a
 async def parallel(self,b):
  limit=b.tolerance;ok=all(abs(x)<=limit for x in (b.gross_variance,b.tax_variance,b.net_variance));return await self.save(ParallelPayrollRun(tenant_id=self.ctx.tenant_id,internal_run_id=b.internal_run_id,external_import_id=b.external_import_id,gross_variance=b.gross_variance,tax_variance=b.tax_variance,net_variance=b.net_variance,status='accepted' if ok else 'exception'),'parallel_payroll')
 async def dashboard(self):
  async def total(m,col,*c):return Decimal(str((await self.db.scalar(select(func.coalesce(func.sum(col),0)).where(m.tenant_id==self.ctx.tenant_id,*c))) or 0))
  return {'open_payroll_liabilities':await total(PayrollLiability,PayrollLiability.open_amount,PayrollLiability.status!='paid'),'open_tax_liabilities':await total(TaxLiability,TaxLiability.open_amount,TaxLiability.status!='paid'),'pending_payments':await total(PayrollPayment,PayrollPayment.amount,PayrollPayment.status!='paid'),'open_tax_notices':int((await self.db.scalar(select(func.count()).select_from(TaxNotice).where(TaxNotice.tenant_id==self.ctx.tenant_id,TaxNotice.status!='resolved'))) or 0)}
 async def negative_net_check(self,run_id):
  rows=list((await self.db.scalars(select(PayrollRunWorker).where(PayrollRunWorker.payroll_run_id==run_id,PayrollRunWorker.tenant_id==self.ctx.tenant_id,PayrollRunWorker.net_pay<0))).all());return {'valid':not rows,'negative_worker_ids':[str(x.worker_id) for x in rows]}

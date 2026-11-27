from __future__ import annotations
import json
from decimal import Decimal
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change
from flowforge.bg08_final.models import AssetTransaction,BillingRun,Entitlement,Plan,Project,ProjectExpense,ProjectTime,Subscription
from flowforge.phase3b.models import CustomerInvoice
from flowforge.finance_final.service import FinalFinanceService
from .models import BG08Execution,BillingRunItem,ProjectBilling,SubscriptionAmendment
class CompletionService:
 def __init__(self,db:AsyncSession,ctx:TenantContext):self.db=db;self.ctx=ctx
 async def save(self,o,e):self.db.add(o);await self.db.flush();await record_change(self.db,self.ctx.tenant_id,self.ctx.user_id,'created',e,str(o.id));await self.db.commit();await self.db.refresh(o);return o
 async def idem(self,op,key,typ,id,result):
  old=await self.db.scalar(select(BG08Execution).where(BG08Execution.tenant_id==self.ctx.tenant_id,BG08Execution.operation==op,BG08Execution.idempotency_key==key))
  if old:return old,True
  x=BG08Execution(tenant_id=self.ctx.tenant_id,operation=op,idempotency_key=key,aggregate_type=typ,aggregate_id=id,result_json=json.dumps(result,default=str),actor_user_id=self.ctx.user_id);self.db.add(x);return x,False
 async def amend(self,sid,b):
  s=await self.db.scalar(select(Subscription).where(Subscription.id==sid,Subscription.tenant_id==self.ctx.tenant_id).with_for_update());
  if not s:raise LookupError('Subscription not found')
  p=await self.db.scalar(select(Plan).where(Plan.id==s.plan_id,Plan.tenant_id==self.ctx.tenant_id));days=30;remaining=max(Decimal('0'),Decimal((s.renews_on-b.effective_date).days if s.renews_on else days));proration=((b.new_quantity-s.quantity)*p.price*remaining/Decimal(days)).quantize(Decimal('.01'));a=SubscriptionAmendment(tenant_id=self.ctx.tenant_id,subscription_id=s.id,amendment_type=b.amendment_type,effective_date=b.effective_date,old_quantity=s.quantity,new_quantity=b.new_quantity,proration_amount=proration,status='approved',approved_by=self.ctx.user_id);s.quantity=b.new_quantity;await self.save(a,'subscription_amendment');return a
 async def enforce(self,sid,code,consume):
  e=await self.db.scalar(select(Entitlement).where(Entitlement.subscription_id==sid,Entitlement.tenant_id==self.ctx.tenant_id,Entitlement.code==code,Entitlement.active.is_(True)).with_for_update());
  if not e:raise PermissionError('Entitlement unavailable')
  if e.limit_value is not None and e.consumed_value+consume>e.limit_value:raise PermissionError('Entitlement limit exceeded')
  e.consumed_value+=consume;await self.db.commit();return e
 async def execute_billing(self,rid,key):
  run=await self.db.scalar(select(BillingRun).where(BillingRun.id==rid,BillingRun.tenant_id==self.ctx.tenant_id).with_for_update());
  if not run:raise LookupError('Billing run not found')
  _,dup=await self.idem('billing_execute',key,'billing_run',rid,{})
  if dup:return {'idempotent':True}
  items=list((await self.db.scalars(select(BillingRunItem).where(BillingRunItem.billing_run_id==rid,BillingRunItem.tenant_id==self.ctx.tenant_id))).all());run.status='completed';run.invoice_count=len(items);run.total_amount=sum((x.amount for x in items),Decimal('0'));await self.db.commit();return {'items':len(items),'total':run.total_amount}
 async def project_bill(self,b):
  _,dup=await self.idem('project_bill',b.idempotency_key,'project',b.project_id,{})
  if dup:return {'idempotent':True}
  time=Decimal(str((await self.db.scalar(select(func.coalesce(func.sum(ProjectTime.hours*ProjectTime.rate),0)).where(ProjectTime.tenant_id==self.ctx.tenant_id,ProjectTime.project_id==b.project_id,ProjectTime.work_date>=b.period_start,ProjectTime.work_date<=b.period_end,ProjectTime.status=='approved',ProjectTime.billable.is_(True)))) or 0));expense=Decimal(str((await self.db.scalar(select(func.coalesce(func.sum(ProjectExpense.amount),0)).where(ProjectExpense.tenant_id==self.ctx.tenant_id,ProjectExpense.project_id==b.project_id,ProjectExpense.expense_date>=b.period_start,ProjectExpense.expense_date<=b.period_end,ProjectExpense.status=='approved',ProjectExpense.billable.is_(True)))) or 0));x=ProjectBilling(tenant_id=self.ctx.tenant_id,project_id=b.project_id,period_start=b.period_start,period_end=b.period_end,status='calculated',billable_time=time,billable_expenses=expense,revenue_recognized=time+expense);return await self.save(x,'project_billing')
 async def asset_post(self,txn_id,b):
  t=await self.db.scalar(select(AssetTransaction).where(AssetTransaction.id==txn_id,AssetTransaction.tenant_id==self.ctx.tenant_id));
  if not t:raise LookupError('Asset transaction not found')
  finance=FinalFinanceService(self.db,self.ctx);out=await finance.journal(kind=f'bg08_asset_{t.transaction_type}',key=b.idempotency_key,ledger_id=b.ledger_id,period_id=b.period_id,journal_date=b.transaction_date,description=f'Asset {t.transaction_type}',lines=[(b.debit_account_id,b.amount,Decimal('0')),(b.credit_account_id,Decimal('0'),b.amount)]);t.journal_id=__import__('uuid').UUID(out['journal_id']);await self.db.commit();return out

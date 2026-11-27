from __future__ import annotations
import json
from decimal import Decimal
from uuid import UUID
from sqlalchemy import func,or_,select
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change
from flowforge.crm_sales.models import Campaign,Communication,CreditProfile,Lead,Opportunity,Quote,QuoteLine
from flowforge.phase3b.models import CustomerInvoice,SalesOrder
from .models import *
class CRMCompletionService:
 def __init__(self,db:AsyncSession,ctx:TenantContext):self.db=db;self.ctx=ctx
 async def save(self,o,e):self.db.add(o);await self.db.flush();await record_change(self.db,self.ctx.tenant_id,self.ctx.user_id,'created',e,str(o.id));await self.db.commit();await self.db.refresh(o);return o
 async def event(self,t,a,id,p):self.db.add(CRMEvent(tenant_id=self.ctx.tenant_id,event_type=t,aggregate_type=a,aggregate_id=id,payload_json=json.dumps(p,default=str)))
 async def execution(self,op,key,typ,id,result):
  old=await self.db.scalar(select(CRMExecution).where(CRMExecution.tenant_id==self.ctx.tenant_id,CRMExecution.operation==op,CRMExecution.idempotency_key==key))
  if old:return old,True
  x=CRMExecution(tenant_id=self.ctx.tenant_id,operation=op,idempotency_key=key,entity_type=typ,entity_id=id,result_json=json.dumps(result,default=str),actor_user_id=self.ctx.user_id);self.db.add(x);return x,False
 async def price(self,b):
  stmt=select(PriceListItem,PriceList).join(PriceList,PriceList.id==PriceListItem.price_list_id).where(PriceListItem.tenant_id==self.ctx.tenant_id,PriceList.tenant_id==self.ctx.tenant_id,PriceList.active.is_(True),PriceList.currency_code==b.currency_code,PriceListItem.product_id==b.product_id,PriceListItem.min_quantity<=b.quantity,or_(PriceList.customer_id==b.customer_id,PriceList.customer_id.is_(None))).order_by(PriceList.customer_id.desc().nullslast(),PriceListItem.min_quantity.desc())
  row=(await self.db.execute(stmt)).first()
  if not row:raise LookupError('No applicable price')
  i,p=row;gross=b.quantity*i.unit_price;discount=gross*Decimal(i.discount_bps)/Decimal(10000);return {'price_list_id':str(p.id),'unit_price':i.unit_price,'discount_bps':i.discount_bps,'total':gross-discount}
 async def revise_quote(self,qid,reason,key):
  q=await self.db.scalar(select(Quote).where(Quote.id==qid,Quote.tenant_id==self.ctx.tenant_id));
  if not q:raise LookupError('Quote not found')
  old,dup=await self.execution('quote_revision',key,'quote',qid,{'quote_id':str(qid)})
  if dup:return old
  count=int((await self.db.scalar(select(func.count()).select_from(QuoteRevision).where(QuoteRevision.quote_id==qid,QuoteRevision.tenant_id==self.ctx.tenant_id))) or 0)
  lines=list((await self.db.scalars(select(QuoteLine).where(QuoteLine.quote_id==qid,QuoteLine.tenant_id==self.ctx.tenant_id))).all());snap={'quote':{c.name:str(getattr(q,c.name)) for c in q.__table__.columns},'lines':[{c.name:str(getattr(l,c.name)) for c in l.__table__.columns} for l in lines]}
  r=QuoteRevision(tenant_id=self.ctx.tenant_id,quote_id=qid,revision_number=count+1,snapshot_json=json.dumps(snap),reason=reason,created_by=self.ctx.user_id);self.db.add(r);q.status='draft';await self.event('quote.revised','quote',qid,{'revision':count+1});await self.db.commit();return r
 async def recompute_credit(self,party_id):
  c=await self.db.scalar(select(CreditProfile).where(CreditProfile.party_id==party_id,CreditProfile.tenant_id==self.ctx.tenant_id));
  if not c:raise LookupError('Credit profile not found')
  invoices=Decimal(str((await self.db.scalar(select(func.coalesce(func.sum(CustomerInvoice.balance_due),0)).where(CustomerInvoice.tenant_id==self.ctx.tenant_id,CustomerInvoice.customer_id==party_id))) or 0));orders=Decimal(str((await self.db.scalar(select(func.coalesce(func.sum(SalesOrder.total_amount),0)).where(SalesOrder.tenant_id==self.ctx.tenant_id,SalesOrder.customer_id==party_id,SalesOrder.status.in_(['draft','confirmed','allocated'])))) or 0));c.current_exposure=invoices+orders;c.status='hold' if c.current_exposure>c.credit_limit else 'active';c.hold_reason='Exposure exceeds credit limit' if c.status=='hold' else None;await self.db.commit();return c
 async def search(self,model,b,fields):
  stmt=select(model).where(model.tenant_id==self.ctx.tenant_id)
  if b.query:stmt=stmt.where(or_(*[getattr(model,f).ilike(f'%{b.query}%') for f in fields]))
  return list((await self.db.scalars(stmt.offset(b.offset).limit(b.limit))).all())
 async def funnel(self):
  rows=(await self.db.execute(select(Opportunity.stage,func.count(),func.coalesce(func.sum(Opportunity.amount),0)).where(Opportunity.tenant_id==self.ctx.tenant_id).group_by(Opportunity.stage))).all();return [{'stage':s,'count':c,'amount':a} for s,c,a in rows]

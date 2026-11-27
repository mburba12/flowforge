from __future__ import annotations
from decimal import Decimal
from uuid import UUID
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase2b.models import AccountBalance,AccountingPeriod,JournalEntry,JournalLine
from flowforge.phase3a.models import APOpenItem,GoodsReceipt,PurchaseOrder,VendorInvoice
from flowforge.phase3b.models import AROpenItem,CustomerInvoice,CustomerReceipt,SalesOrder,Shipment
class FinanceWorkflowService:
 def __init__(self,db:AsyncSession,ctx:TenantContext):self.db=db;self.ctx=ctx
 async def _count(self,model,*conditions)->int:return int((await self.db.scalar(select(func.count()).select_from(model).where(model.tenant_id==self.ctx.tenant_id,*conditions))) or 0)
 async def _sum(self,model,column,*conditions)->Decimal:return Decimal(str((await self.db.scalar(select(func.coalesce(func.sum(column),0)).select_from(model).where(model.tenant_id==self.ctx.tenant_id,*conditions))) or 0))
 async def procure_to_pay(self)->dict[str,object]:
  metrics={'purchase_orders':await self._count(PurchaseOrder),'receipts':await self._count(GoodsReceipt),'vendor_invoices':await self._count(VendorInvoice),'open_ap_items':await self._count(APOpenItem,APOpenItem.status!='paid'),'open_ap_balance':await self._sum(APOpenItem,APOpenItem.open_amount,APOpenItem.status!='paid')}
  blockers=[]
  if metrics['purchase_orders'] and not metrics['receipts']:blockers.append('Purchase orders exist without receipts')
  if metrics['receipts'] and not metrics['vendor_invoices']:blockers.append('Receipts exist without vendor invoices')
  return {'workflow':'procure_to_pay','ready':not blockers,'blockers':blockers,'metrics':metrics}
 async def order_to_cash(self)->dict[str,object]:
  metrics={'sales_orders':await self._count(SalesOrder),'shipments':await self._count(Shipment),'customer_invoices':await self._count(CustomerInvoice),'receipts':await self._count(CustomerReceipt),'open_ar_items':await self._count(AROpenItem,AROpenItem.status!='paid'),'open_ar_balance':await self._sum(AROpenItem,AROpenItem.open_amount,AROpenItem.status!='paid')}
  blockers=[]
  if metrics['sales_orders'] and not metrics['shipments']:blockers.append('Sales orders exist without shipments')
  if metrics['shipments'] and not metrics['customer_invoices']:blockers.append('Shipments exist without customer invoices')
  return {'workflow':'order_to_cash','ready':not blockers,'blockers':blockers,'metrics':metrics}
 async def close_assessment(self,ledger_id:UUID,period_id:UUID,tolerance:Decimal)->dict[str,object]:
  period=await self.db.scalar(select(AccountingPeriod).where(AccountingPeriod.id==period_id,AccountingPeriod.tenant_id==self.ctx.tenant_id))
  if period is None:raise LookupError('Accounting period not found')
  balances=list((await self.db.scalars(select(AccountBalance).where(AccountBalance.tenant_id==self.ctx.tenant_id,AccountBalance.ledger_id==ledger_id,AccountBalance.period_id==period_id))).all())
  debit=sum((Decimal(str(x.debit_total)) for x in balances),Decimal('0'));credit=sum((Decimal(str(x.credit_total)) for x in balances),Decimal('0'));variance=debit-credit
  draft=await self._count(JournalEntry,JournalEntry.ledger_id==ledger_id,JournalEntry.period_id==period_id,JournalEntry.status!='posted')
  ap=await self._sum(APOpenItem,APOpenItem.open_amount,APOpenItem.status!='paid');ar=await self._sum(AROpenItem,AROpenItem.open_amount,AROpenItem.status!='paid')
  blockers=[]
  if abs(variance)>tolerance:blockers.append('Trial balance variance exceeds tolerance')
  if draft:blockers.append('Unposted journals remain')
  return {'workflow':'period_close','ready':not blockers,'blockers':blockers,'metrics':{'period_status':period.status,'debit':debit,'credit':credit,'variance':variance,'unposted_journals':draft,'open_ap':ap,'open_ar':ar}}
 def reconcile(self,source:Decimal,target:Decimal,tolerance:Decimal,source_name:str,target_name:str)->dict[str,object]:
  variance=source-target;ready=abs(variance)<=tolerance
  return {'workflow':'reconciliation','ready':ready,'blockers':[] if ready else [f'{source_name} and {target_name} differ beyond tolerance'],'metrics':{'source_name':source_name,'target_name':target_name,'source_balance':source,'target_balance':target,'variance':variance,'tolerance':tolerance}}
 async def finance_health(self)->dict[str,object]:
  result=await self.db.execute(select(JournalLine.journal_id,func.coalesce(func.sum(JournalLine.debit),0),func.coalesce(func.sum(JournalLine.credit),0)).where(JournalLine.tenant_id==self.ctx.tenant_id).group_by(JournalLine.journal_id));bad=[str(i) for i,d,c in result.all() if d!=c]
  return {'healthy':not bad,'unbalanced_journal_ids':bad,'unbalanced_count':len(bad)}

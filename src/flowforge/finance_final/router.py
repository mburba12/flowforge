from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.core.security import Principal,current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext
from .schemas import *
from .service import FinalFinanceService
router=APIRouter(prefix='/api/v2/finance/final',tags=['finance-final'])
P=Annotated[Principal,Depends(current_principal)];D=Annotated[AsyncSession,Depends(get_tenant_db)]
def svc(p:P,db:D):return FinalFinanceService(db,TenantContext(p.tenant_id,p.user_id))
def wrap(e):return HTTPException(404 if isinstance(e,LookupError) else 409,str(e))
@router.post('/recurring/{rid}/post')
async def recurring(rid:UUID,b:Execute,s:Annotated[FinalFinanceService,Depends(svc)]):
 try:return await s.recurring(rid,b.idempotency_key,b.period_id,b.journal_date)
 except Exception as e:raise wrap(e) from e
@router.post('/accruals/{aid}/post')
async def accrual(aid:UUID,b:Execute,s:Annotated[FinalFinanceService,Depends(svc)]):
 try:return await s.accrual(aid,b.idempotency_key,b.period_id,b.journal_date)
 except Exception as e:raise wrap(e) from e
@router.post('/allocations/post')
async def allocation(b:AllocationExecute,s:Annotated[FinalFinanceService,Depends(svc)]):
 try:return await s.allocation(b)
 except Exception as e:raise wrap(e) from e
@router.post('/payment-batches/{bid}/apply')
async def apply(bid:UUID,b:PaymentAction,s:Annotated[FinalFinanceService,Depends(svc)]):
 try:return await s.payment(bid,b)
 except Exception as e:raise wrap(e) from e
@router.post('/payment-batches/{bid}/reverse')
async def reverse(bid:UUID,b:PaymentAction,s:Annotated[FinalFinanceService,Depends(svc)]):
 try:return await s.payment(bid,b,True)
 except Exception as e:raise wrap(e) from e
@router.post('/reconciliations/{sid}/match')
async def match(sid:UUID,b:MatchAction,s:Annotated[FinalFinanceService,Depends(svc)]):
 try:return await s.match(sid,b.item_ids,b.target_reference)
 except Exception as e:raise wrap(e) from e
@router.post('/reconciliations/{sid}/unmatch')
async def unmatch(sid:UUID,b:MatchAction,s:Annotated[FinalFinanceService,Depends(svc)]):
 try:return await s.match(sid,b.item_ids,b.target_reference,True)
 except Exception as e:raise wrap(e) from e
@router.post('/assets/{asset_id}/post')
async def asset(asset_id:UUID,b:AssetPosting,s:Annotated[FinalFinanceService,Depends(svc)]):
 try:return await s.asset_post(asset_id,b)
 except Exception as e:raise wrap(e) from e
@router.post('/reports')
async def reports(b:ReportRequest,s:Annotated[FinalFinanceService,Depends(svc)]):return await s.reports(b)

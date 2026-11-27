from __future__ import annotations
import json
from datetime import UTC,datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change
from flowforge.foundation_completion.models import AccessReview,DataQualityIssue,DataQualityRule,ExportJob,ModuleEntitlement,StewardshipTask,SupportGrant
from flowforge.phase2a.models import Address,ContactMethod,Identifier,OrganizationUnit,Party,PartyRelationship,PartyRoleAssignment,PaymentTerm
from .models import *
class FinalFoundationService:
 def __init__(self,db:AsyncSession,ctx:TenantContext):self.db=db;self.ctx=ctx
 async def save(self,o,e):self.db.add(o);await self.db.flush();await record_change(self.db,self.ctx.tenant_id,self.ctx.user_id,'created',e,str(o.id));await self.db.commit();await self.db.refresh(o);return o
 async def decide(self,model,id,decision,reason):
  o=await self.db.scalar(select(model).where(model.id==id,model.tenant_id==self.ctx.tenant_id));
  if not o:raise LookupError('Record not found')
  if hasattr(o,'status'):o.status={'approve':'approved','reject':'rejected','complete':'completed','remediate':'remediated','revoke':'revoked','archive':'archived','reactivate':'active','verify':'verified','deactivate':'inactive'}[decision]
  if hasattr(o,'resolution'):o.resolution=reason
  if hasattr(o,'decision_json'):o.decision_json=json.dumps({'decision':decision,'reason':reason,'actor':str(self.ctx.user_id)})
  if decision=='complete' and hasattr(o,'completed_at'):o.completed_at=datetime.now(UTC)
  if decision=='revoke' and hasattr(o,'revoked_at'):o.revoked_at=datetime.now(UTC)
  await record_change(self.db,self.ctx.tenant_id,self.ctx.user_id,decision,model.__tablename__,str(id));await self.db.commit();return o
 async def hierarchy_reparent(self,unit_id,parent_id):
  unit=await self.db.scalar(select(OrganizationUnit).where(OrganizationUnit.id==unit_id,OrganizationUnit.tenant_id==self.ctx.tenant_id))
  if not unit:raise LookupError('Organization unit not found')
  if unit_id==parent_id:raise ValueError('Unit cannot parent itself')
  seen={unit_id};cur=parent_id
  while cur:
   if cur in seen:raise ValueError('Hierarchy cycle detected')
   seen.add(cur);p=await self.db.scalar(select(OrganizationUnit).where(OrganizationUnit.id==cur,OrganizationUnit.tenant_id==self.ctx.tenant_id));cur=p.parent_id if p else None
  unit.parent_id=parent_id;await self.db.commit();return unit
 async def import_job(self,b):return await self.save(ImportJob(tenant_id=self.ctx.tenant_id,entity_type=b.entity_type,source_reference=b.source_reference,mapping_json=json.dumps(b.mapping),requested_by=self.ctx.user_id),'import_job')
 async def quality_run(self,rule_id,entity_id,passed,details):
  rule=await self.db.scalar(select(DataQualityRule).where(DataQualityRule.id==rule_id,DataQualityRule.tenant_id==self.ctx.tenant_id,DataQualityRule.active.is_(True)))
  if not rule:raise LookupError('Active quality rule not found')
  if passed:return {'passed':True,'issue_id':None}
  issue=DataQualityIssue(tenant_id=self.ctx.tenant_id,rule_id=rule_id,entity_id=entity_id,details_json=json.dumps(details));await self.save(issue,'data_quality_issue');return {'passed':False,'issue_id':str(issue.id)}
 async def index(self,b):
  old=await self.db.scalar(select(SearchIndexItem).where(SearchIndexItem.tenant_id==self.ctx.tenant_id,SearchIndexItem.entity_type==b.entity_type,SearchIndexItem.entity_id==b.entity_id))
  if old:old.document_json=json.dumps(b.document);old.version+=1;old.stale=False;await self.db.commit();return old
  return await self.save(SearchIndexItem(tenant_id=self.ctx.tenant_id,entity_type=b.entity_type,entity_id=b.entity_id,document_json=json.dumps(b.document)),'search_index')

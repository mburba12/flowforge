from __future__ import annotations
import json
from datetime import UTC,datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change
from .models import *
class FoundationService:
 def __init__(self,db:AsyncSession,ctx:TenantContext):self.db=db;self.ctx=ctx
 async def save(self,o,e):self.db.add(o);await self.db.flush();await record_change(self.db,self.ctx.tenant_id,self.ctx.user_id,'created',e,str(o.id));await self.db.commit();await self.db.refresh(o);return o
 async def entitlement(self,module,deps):return await self.save(ModuleEntitlement(tenant_id=self.ctx.tenant_id,module_code=module,dependencies_json=json.dumps(deps)),'module_entitlement')
 async def disable(self,eid):
  e=await self.db.scalar(select(ModuleEntitlement).where(ModuleEntitlement.id==eid,ModuleEntitlement.tenant_id==self.ctx.tenant_id));
  if not e:raise LookupError('Entitlement not found')
  children=list((await self.db.scalars(select(ModuleEntitlement).where(ModuleEntitlement.tenant_id==self.ctx.tenant_id,ModuleEntitlement.status=='enabled'))).all())
  if any(e.module_code in json.loads(x.dependencies_json) for x in children):raise ValueError('Enabled modules depend on this module')
  e.status='disabled';await self.db.commit();return e
 async def support(self,b):
  if b.expires_at<=datetime.now(UTC):raise ValueError('Support grant expiration must be future')
  return await self.save(SupportGrant(tenant_id=self.ctx.tenant_id,support_user_id=b.support_user_id,scope_json=json.dumps(b.scope),reason=b.reason,expires_at=b.expires_at,approved_by=b.approved_by),'support_grant')
 async def list(self,m):return list((await self.db.scalars(select(m).where(m.tenant_id==self.ctx.tenant_id))).all())

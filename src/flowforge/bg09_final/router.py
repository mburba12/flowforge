import json
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from flowforge.core.security import Principal,current_principal
from flowforge.db.session import get_tenant_db
from .models import ManufacturingRecord,GenealogyEdge
from .schemas import RecordCreate,Transition,GenealogyCreate
router=APIRouter(prefix="/api/v2/bg09",tags=["bg09-manufacturing-quality"])
P=Annotated[Principal,Depends(current_principal)];D=Annotated[AsyncSession,Depends(get_tenant_db)]
@router.post("/records",status_code=201)
async def create(b:RecordCreate,p:P,db:D):
 x=ManufacturingRecord(tenant_id=p.tenant_id,record_type=b.record_type,code=b.code,payload_json=json.dumps(b.payload),parent_id=b.parent_id);db.add(x);await db.commit();await db.refresh(x);return x
@router.post("/records/{id}/transition")
async def transition(id:UUID,b:Transition,p:P,db:D):
 x=await db.scalar(select(ManufacturingRecord).where(ManufacturingRecord.id==id,ManufacturingRecord.tenant_id==p.tenant_id));
 if not x:raise HTTPException(404,"Record not found")
 allowed={"draft":{"submitted","cancelled"},"submitted":{"approved","rejected"},"approved":{"released","closed","recalled"},"released":{"completed","closed","recalled"},"open":{"investigating","contained","closed"},"investigating":{"contained","corrective_action","closed"},"corrective_action":{"verification","closed"},"verification":{"closed"}}
 if b.target not in allowed.get(x.status,set()):raise HTTPException(409,f"Invalid transition {x.status}->{b.target}")
 if b.target=="approved":x.approved_by=p.user_id
 x.status=b.target;await db.commit();return x
@router.post("/genealogy",status_code=201)
async def genealogy(b:GenealogyCreate,p:P,db:D):
 if b.parent_lot==b.child_lot:raise HTTPException(422,"Self genealogy forbidden")
 x=GenealogyEdge(tenant_id=p.tenant_id,parent_lot=b.parent_lot,child_lot=b.child_lot,work_order_code=b.work_order_code,payload_json=json.dumps(b.payload));db.add(x);await db.commit();return x

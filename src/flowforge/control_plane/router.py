from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException
from flowforge.core.security import Principal,current_principal
from .capabilities import CAPABILITIES,registry
router=APIRouter(prefix='/control-plane',tags=['control-plane'])
P=Annotated[Principal,Depends(current_principal)]
@router.get('/capabilities')
async def capabilities(p:P)->dict[str,object]:return {'tenant_id':str(p.tenant_id),'count':len(CAPABILITIES),'items':[x.to_dict() for x in CAPABILITIES]}
@router.get('/capabilities/{code}')
async def capability(code:str,p:P)->dict[str,object]:
 item=registry().get(code)
 if item is None:raise HTTPException(404,'Capability not found')
 return {'tenant_id':str(p.tenant_id),**item.to_dict()}
@router.get('/readiness')
async def readiness(p:P)->dict[str,object]:
 unavailable=[x.code for x in CAPABILITIES if not x.available()]
 return {'tenant_id':str(p.tenant_id),'ready':not unavailable,'unavailable':unavailable}

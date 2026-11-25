from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .schemas import GLMappingCreate, LinkSessionCreate, ManualTransactionCreate, TokenExchange
from .service import BankingError, BankingService

router = APIRouter(prefix="/api/v4c", tags=["phase4c-banking"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(p: P, db: D) -> BankingService:
    return BankingService(db, p.tenant_id, p.user_id)


S = Annotated[BankingService, Depends(service)]


@router.post("/connections/link-session")
async def link(body: LinkSessionCreate, s: S) -> dict[str, str]:
    return {"link_token": await s.link_session(body.provider)}


@router.post("/connections/exchange", status_code=201)
async def exchange(body: TokenExchange, s: S) -> dict[str, str]:
    try:
        x = await s.exchange(body)
    except (BankingError, ValueError) as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(x.id), "status": x.status, "provider": x.provider}


@router.put("/accounts/{account_id}/gl-mapping")
async def mapping(account_id: UUID, body: GLMappingCreate, s: S) -> dict[str, str]:
    try:
        x = await s.map_account(account_id, body)
    except BankingError as e:
        raise HTTPException(404, str(e)) from e
    return {"id": str(x.id), "mapping_type": x.mapping_type}


@router.post("/transactions/manual", status_code=201)
async def manual(body: ManualTransactionCreate, s: S) -> dict[str, str]:
    try:
        x = await s.manual_transaction(body)
    except BankingError as e:
        raise HTTPException(404, str(e)) from e
    return {"id": str(x.id), "amount": str(x.amount)}


@router.post("/connections/{connection_id}/sync")
async def sync(connection_id: UUID, s: S) -> dict[str, str]:
    try:
        x = await s.sync(connection_id)
    except BankingError as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(x.id), "status": x.status, "created": str(x.transactions_created)}

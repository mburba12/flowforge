from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .catalog import provider_codes
from .schemas import CommerceConnectionCreate, CommerceSyncRequest, CommerceWebhookIngest
from .service import CommerceIntegrationError, CommerceIntegrationService

router = APIRouter(prefix="/api/v4c/commerce", tags=["phase4c-commerce"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(p: P, db: D) -> CommerceIntegrationService:
    return CommerceIntegrationService(db, p.tenant_id, p.user_id)


S = Annotated[CommerceIntegrationService, Depends(service)]


@router.get("/providers")
async def providers() -> dict[str, tuple[str, ...]]:
    return {"providers": provider_codes()}


@router.post("/connections", status_code=201)
async def connect(body: CommerceConnectionCreate, s: S) -> dict[str, str]:
    try:
        x = await s.connect(body)
    except (CommerceIntegrationError, ValueError) as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(x.id), "status": x.status, "provider": x.provider, "store_name": x.store_name}


@router.post("/connections/{connection_id}/sync")
async def sync(connection_id: UUID, body: CommerceSyncRequest, s: S) -> dict[str, int]:
    try:
        return await s.sync(connection_id)
    except CommerceIntegrationError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/connections/{connection_id}/webhooks", status_code=202)
async def webhook(connection_id: UUID, body: CommerceWebhookIngest, s: S) -> dict[str, str]:
    try:
        x = await s.webhook(connection_id, body)
    except CommerceIntegrationError as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(x.id), "status": "processed"}

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .schemas import PaymentConnectionCreate, PaymentSyncRequest, WebhookIngest
from .service import PaymentIntegrationError, PaymentIntegrationService

router = APIRouter(prefix="/api/v4c/payments", tags=["phase4c-payments"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(p: P, db: D) -> PaymentIntegrationService:
    return PaymentIntegrationService(db, p.tenant_id, p.user_id)


S = Annotated[PaymentIntegrationService, Depends(service)]


@router.post("/connections", status_code=201)
async def connect(body: PaymentConnectionCreate, s: S) -> dict[str, str]:
    try:
        x = await s.connect(body)
    except (PaymentIntegrationError, ValueError) as e:
        raise HTTPException(409, str(e)) from e
    return {
        "id": str(x.id),
        "status": x.status,
        "provider": x.provider,
        "environment": x.environment,
    }


@router.post("/connections/{connection_id}/sync")
async def sync(connection_id: UUID, body: PaymentSyncRequest, s: S) -> dict[str, int]:
    try:
        return await s.sync(connection_id)
    except PaymentIntegrationError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/connections/{connection_id}/webhooks", status_code=202)
async def webhook(connection_id: UUID, body: WebhookIngest, s: S) -> dict[str, str]:
    try:
        x = await s.webhook(connection_id, body)
    except PaymentIntegrationError as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(x.id), "status": "processed"}

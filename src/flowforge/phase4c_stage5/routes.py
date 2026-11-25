from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .catalog import provider_codes
from .schemas import FinanceConnectionCreate, FinanceSyncRequest, FinanceWebhookIngest
from .service import FinanceIntegrationError, FinanceIntegrationService

router = APIRouter(prefix="/api/v4c/finance", tags=["phase4c-finance"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(p: P, db: D) -> FinanceIntegrationService:
    return FinanceIntegrationService(db, p.tenant_id, p.user_id)


S = Annotated[FinanceIntegrationService, Depends(service)]


@router.get("/providers")
async def providers() -> dict[str, tuple[str, ...]]:
    return {"providers": provider_codes()}


@router.post("/connections", status_code=201)
async def connect(body: FinanceConnectionCreate, s: S) -> dict[str, str]:
    try:
        x = await s.connect(body)
    except (FinanceIntegrationError, ValueError) as e:
        raise HTTPException(409, str(e)) from e
    return {
        "id": str(x.id),
        "status": x.status,
        "provider": x.provider,
        "organization_name": x.organization_name,
    }


@router.post("/connections/{connection_id}/sync")
async def sync(connection_id: UUID, body: FinanceSyncRequest, s: S) -> dict[str, int]:
    try:
        return await s.sync(connection_id)
    except FinanceIntegrationError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/connections/{connection_id}/webhooks", status_code=202)
async def webhook(connection_id: UUID, body: FinanceWebhookIngest, s: S) -> dict[str, str]:
    try:
        x = await s.webhook(connection_id, body)
    except FinanceIntegrationError as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(x.id), "status": "processed"}

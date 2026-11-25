from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .catalog import provider_codes
from .schemas import (
    EngagementConnectionCreate,
    EngagementSyncRequest,
    EngagementWebhookIngest,
)
from .service import EngagementIntegrationError, EngagementIntegrationService

router = APIRouter(prefix="/api/v4c/engagement", tags=["phase4c-engagement"])
PrincipalDependency = Annotated[Principal, Depends(current_principal)]
DatabaseDependency = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(principal: PrincipalDependency, db: DatabaseDependency) -> EngagementIntegrationService:
    return EngagementIntegrationService(db, principal.tenant_id, principal.user_id)


ServiceDependency = Annotated[EngagementIntegrationService, Depends(service)]


@router.get("/providers")
async def providers() -> dict[str, tuple[str, ...]]:
    return {"providers": provider_codes()}


@router.post("/connections", status_code=201)
async def connect(
    body: EngagementConnectionCreate, integration: ServiceDependency
) -> dict[str, str]:
    try:
        connection = await integration.connect(body)
    except (EngagementIntegrationError, ValueError) as error:
        raise HTTPException(409, str(error)) from error
    return {
        "id": str(connection.id),
        "status": connection.status,
        "provider": connection.provider,
        "organization_name": connection.organization_name,
    }


@router.post("/connections/{connection_id}/sync")
async def sync(
    connection_id: UUID, body: EngagementSyncRequest, integration: ServiceDependency
) -> dict[str, int]:
    try:
        return await integration.sync(connection_id)
    except EngagementIntegrationError as error:
        raise HTTPException(404, str(error)) from error


@router.post("/connections/{connection_id}/webhooks", status_code=202)
async def webhook(
    connection_id: UUID, body: EngagementWebhookIngest, integration: ServiceDependency
) -> dict[str, str]:
    try:
        event = await integration.webhook(connection_id, body)
    except EngagementIntegrationError as error:
        raise HTTPException(409, str(error)) from error
    return {"id": str(event.id), "status": "processed"}

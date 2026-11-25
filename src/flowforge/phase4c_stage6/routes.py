from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .catalog import provider_codes
from .schemas import (
    WorkforceConnectionCreate,
    WorkforceSyncRequest,
    WorkforceWebhookIngest,
)
from .service import WorkforceIntegrationError, WorkforceIntegrationService

router = APIRouter(prefix="/api/v4c/workforce", tags=["phase4c-workforce"])
PrincipalDependency = Annotated[Principal, Depends(current_principal)]
DatabaseDependency = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(principal: PrincipalDependency, db: DatabaseDependency) -> WorkforceIntegrationService:
    return WorkforceIntegrationService(db, principal.tenant_id, principal.user_id)


ServiceDependency = Annotated[WorkforceIntegrationService, Depends(service)]


@router.get("/providers")
async def providers() -> dict[str, tuple[str, ...]]:
    return {"providers": provider_codes()}


@router.post("/connections", status_code=201)
async def connect(
    body: WorkforceConnectionCreate, integration: ServiceDependency
) -> dict[str, str]:
    try:
        connection = await integration.connect(body)
    except (WorkforceIntegrationError, ValueError) as error:
        raise HTTPException(409, str(error)) from error
    return {
        "id": str(connection.id),
        "status": connection.status,
        "provider": connection.provider,
        "organization_name": connection.organization_name,
    }


@router.post("/connections/{connection_id}/sync")
async def sync(
    connection_id: UUID, body: WorkforceSyncRequest, integration: ServiceDependency
) -> dict[str, int]:
    try:
        return await integration.sync(connection_id)
    except WorkforceIntegrationError as error:
        raise HTTPException(404, str(error)) from error


@router.post("/connections/{connection_id}/webhooks", status_code=202)
async def webhook(
    connection_id: UUID, body: WorkforceWebhookIngest, integration: ServiceDependency
) -> dict[str, str]:
    try:
        event = await integration.webhook(connection_id, body)
    except WorkforceIntegrationError as error:
        raise HTTPException(409, str(error)) from error
    return {"id": str(event.id), "status": "processed"}

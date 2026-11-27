import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .models import ProviderConnection, ProviderOperation, WebhookReceipt
from .schemas import ConnectionCreate, OperationCreate, StatusAction, WebhookCreate

router = APIRouter(prefix="/api/v2/bg11", tags=["bg11-providers"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


@router.post("/connections", status_code=201)
async def connection(b: ConnectionCreate, p: P, db: D):
    if b.mode == "production":
        raise HTTPException(409, "Production mode requires explicit approval transition")
    x = ProviderConnection(
        tenant_id=p.tenant_id,
        provider_type=b.provider_type,
        provider_code=b.provider_code,
        mode=b.mode,
        configuration_json=json.dumps(b.configuration),
    )
    db.add(x)
    await db.commit()
    return x


@router.post("/connections/{id}/status")
async def status(id: UUID, b: StatusAction, p: P, db: D):
    x = await db.scalar(
        select(ProviderConnection).where(
            ProviderConnection.id == id, ProviderConnection.tenant_id == p.tenant_id
        )
    )
    if not x:
        raise HTTPException(404, "Connection not found")
    allowed = {
        "disabled": {"configured"},
        "configured": {"sandbox_certified", "disabled"},
        "sandbox_certified": {"production_approved", "disabled"},
        "production_approved": {"active", "disabled"},
        "active": {"suspended", "disabled"},
        "suspended": {"active", "disabled"},
    }
    if b.target not in allowed.get(x.status, set()):
        raise HTTPException(409, "Invalid provider transition")
    x.status = b.target
    if b.target == "production_approved":
        x.mode = "production"
    await db.commit()
    return x


@router.post("/operations", status_code=201)
async def operation(b: OperationCreate, p: P, db: D):
    c = await db.scalar(
        select(ProviderConnection).where(
            ProviderConnection.id == b.connection_id, ProviderConnection.tenant_id == p.tenant_id
        )
    )
    if not c:
        raise HTTPException(404, "Connection not found")
    if c.status not in ("sandbox_certified", "active"):
        raise HTTPException(409, "Provider writes disabled")
    x = ProviderOperation(
        tenant_id=p.tenant_id,
        connection_id=c.id,
        operation=b.operation,
        idempotency_key=b.idempotency_key,
        request_json=json.dumps(b.request),
        status="sandbox_queued" if c.mode == "sandbox" else "queued",
    )
    db.add(x)
    await db.commit()
    return x


@router.post("/webhooks", status_code=201)
async def webhook(b: WebhookCreate, p: P, db: D):
    if not b.signature_valid:
        raise HTTPException(401, "Invalid webhook signature")
    x = WebhookReceipt(
        tenant_id=p.tenant_id,
        connection_id=b.connection_id,
        event_id=b.event_id,
        signature_valid=1,
        payload_json=json.dumps(b.payload),
    )
    db.add(x)
    await db.commit()
    return x

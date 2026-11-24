from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_db
from flowforge.platform.models import (
    AuditEntry,
    Document,
    IntegrationConnection,
    Notification,
    Role,
    WorkflowDefinition,
)
from flowforge.platform.schemas import (
    DocumentCreate,
    IntegrationCreate,
    NotificationCreate,
    RoleCreate,
    WorkflowCreate,
)
from flowforge.platform.services import record_change

router = APIRouter(tags=["platform"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_db)]


@router.get("/me")
async def me(p: P) -> dict[str, str]:
    return {"user_id": str(p.user_id), "tenant_id": str(p.tenant_id)}


@router.post("/roles", status_code=201)
async def create_role(body: RoleCreate, p: P, db: D) -> dict[str, str]:
    obj = Role(tenant_id=p.tenant_id, **body.model_dump())
    db.add(obj)
    await db.flush()
    await record_change(db, p.tenant_id, p.user_id, "created", "role", str(obj.id))
    await db.commit()
    return {"id": str(obj.id), "name": obj.name}


@router.get("/audit")
async def audit(p: P, db: D) -> list[dict[str, str]]:
    rows = (
        await db.scalars(
            select(AuditEntry)
            .where(AuditEntry.tenant_id == p.tenant_id)
            .order_by(AuditEntry.occurred_at.desc())
            .limit(100)
        )
    ).all()
    return [
        {"action": x.action, "resource_type": x.resource_type, "resource_id": x.resource_id or ""}
        for x in rows
    ]


@router.post("/workflows", status_code=201)
async def workflow(body: WorkflowCreate, p: P, db: D) -> dict[str, str]:
    obj = WorkflowDefinition(tenant_id=p.tenant_id, **body.model_dump())
    db.add(obj)
    await db.flush()
    await record_change(db, p.tenant_id, p.user_id, "created", "workflow", str(obj.id))
    await db.commit()
    return {"id": str(obj.id)}


@router.post("/documents", status_code=201)
async def document(body: DocumentCreate, p: P, db: D) -> dict[str, str]:
    data = body.model_dump()
    meta = data.pop("metadata")
    obj = Document(tenant_id=p.tenant_id, metadata_json=meta, **data)
    db.add(obj)
    await db.flush()
    await record_change(db, p.tenant_id, p.user_id, "created", "document", str(obj.id))
    await db.commit()
    return {"id": str(obj.id)}


@router.post("/notifications", status_code=201)
async def notification(body: NotificationCreate, p: P, db: D) -> dict[str, str]:
    obj = Notification(tenant_id=p.tenant_id, user_id=p.user_id, **body.model_dump())
    db.add(obj)
    await db.commit()
    return {"id": str(obj.id), "status": obj.status}


@router.post("/integrations", status_code=201)
async def integration(body: IntegrationCreate, p: P, db: D) -> dict[str, str]:
    obj = IntegrationConnection(tenant_id=p.tenant_id, **body.model_dump())
    db.add(obj)
    await db.flush()
    await record_change(db, p.tenant_id, p.user_id, "created", "integration", str(obj.id))
    await db.commit()
    return {"id": str(obj.id), "status": obj.status}

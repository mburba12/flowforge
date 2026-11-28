import csv
import io
import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.platform.models import (
    AuditEntry,
    Document,
    IntegrationConnection,
    Notification,
    Role,
    User,
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
D = Annotated[AsyncSession, Depends(get_tenant_db)]


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


AUDIT_SCREEN_LIMIT = 100


def _audit_query(tenant_id: object) -> Select[AuditEntry, str | None]:
    return (
        select(AuditEntry, User.email)
        .outerjoin(User, User.id == AuditEntry.actor_user_id)
        .where(AuditEntry.tenant_id == tenant_id)
        .order_by(AuditEntry.occurred_at.desc(), AuditEntry.id.desc())
    )


def _audit_row(entry: AuditEntry, email: str | None) -> dict[str, str]:
    return {
        "occurred_at": entry.occurred_at.isoformat() if entry.occurred_at else "",
        "user": email or "",
        "action": entry.action,
        "resource_type": entry.resource_type,
        "resource_id": entry.resource_id or "",
    }


@router.get("/audit")
async def audit(p: P, db: D) -> list[dict[str, str]]:
    """The latest 100 changes (the screen). Every change is in /audit/export."""
    rows = (await db.execute(_audit_query(p.tenant_id).limit(AUDIT_SCREEN_LIMIT))).all()
    return [_audit_row(entry, email) for entry, email in rows]


@router.get("/audit/export")
async def audit_export(p: P, db: D) -> Response:
    """Every audited change of the tenant as a CSV file, newest first."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["occurred_at", "user", "action", "record_type", "record_id", "details"])
    result = await db.stream(_audit_query(p.tenant_id).execution_options(yield_per=1000))
    async for item in result:
        entry, email = item[0], item[1]
        row = _audit_row(entry, email)
        details = json.dumps(entry.payload or {}, default=str, sort_keys=True)
        writer.writerow(
            [
                row["occurred_at"],
                row["user"],
                row["action"],
                row["resource_type"],
                row["resource_id"],
                details,
            ]
        )
    await record_change(db, p.tenant_id, p.user_id, "exported", "audit_trail", "all")
    await db.commit()
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return Response(
        content=buffer.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="flowforge-audit-{stamp}.csv"'},
    )


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

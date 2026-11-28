import hashlib
import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .models import CopilotProposal, InformationRecord
from .schemas import CopilotCreate, InfoCreate, ProposalAction

router = APIRouter(prefix="/api/v2/bg10", tags=["bg10-information-ai"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


@router.post("/records", status_code=201)
async def record(b: InfoCreate, p: P, db: D) -> Any:
    x = InformationRecord(
        tenant_id=p.tenant_id,
        record_type=b.record_type,
        code=b.code,
        payload_json=json.dumps(b.payload),
        permission_code=b.permission_code,
        owner_user_id=p.user_id,
    )
    db.add(x)
    await db.commit()
    return x


@router.get("/search")
async def search(q: str, p: P, db: D) -> Any:
    return list(
        (
            await db.scalars(
                select(InformationRecord)
                .where(
                    InformationRecord.tenant_id == p.tenant_id,
                    or_(
                        InformationRecord.code.ilike(f"%{q}%"),
                        InformationRecord.payload_json.ilike(f"%{q}%"),
                    ),
                )
                .limit(100)
            )
        ).all()
    )


@router.post("/copilot/proposals", status_code=201)
async def proposal(b: CopilotCreate, p: P, db: D) -> Any:
    if b.risk == "high" and not b.citations:
        raise HTTPException(422, "High-risk proposal requires citations")
    x = CopilotProposal(
        tenant_id=p.tenant_id,
        prompt_hash=hashlib.sha256(b.prompt.encode()).hexdigest(),
        context_json=json.dumps(b.context),
        response_json=json.dumps(b.response),
        citations_json=json.dumps(b.citations),
        risk=b.risk,
        cost_micros=b.cost_micros,
    )
    db.add(x)
    await db.commit()
    return x


@router.post("/copilot/proposals/{id}/action")
async def action(id: UUID, b: ProposalAction, p: P, db: D) -> Any:
    x = await db.scalar(
        select(CopilotProposal).where(
            CopilotProposal.id == id, CopilotProposal.tenant_id == p.tenant_id
        )
    )
    if not x:
        raise HTTPException(404, "Proposal not found")
    if b.target == "executed" and x.status != "approved":
        raise HTTPException(409, "Approval required")
    x.status = b.target
    if b.target == "approved":
        x.approved_by = p.user_id
    await db.commit()
    return x

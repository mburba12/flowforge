from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .schemas import (
    EntityCreate,
    MatchRequest,
    MergeProposalCreate,
    ReferenceCreate,
    RelationshipCreate,
)
from .service import Phase4DError, Phase4DService

router = APIRouter(prefix="/api/v4/entities", tags=["phase4d-entities"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(p: P, db: D) -> Phase4DService:
    return Phase4DService(db, p.tenant_id, p.user_id)


S = Annotated[Phase4DService, Depends(service)]


@router.post("", status_code=201)
async def create(body: EntityCreate, s: S) -> dict[str, str]:
    row = await s.create_entity(body)
    return {"id": str(row.id), "status": row.status}


@router.get("/{entity_id}")
async def get(entity_id: UUID, s: S) -> dict[str, object]:
    try:
        row = await s.get_entity(entity_id)
    except Phase4DError as e:
        raise HTTPException(404, str(e)) from e
    return {
        "id": str(row.id),
        "entity_type": row.entity_type,
        "display_name": row.display_name,
        "source_count": row.source_count,
    }


@router.post("/{entity_id}/lineage", status_code=201)
async def lineage(entity_id: UUID, body: ReferenceCreate, s: S) -> dict[str, str]:
    try:
        row = await s.add_reference(entity_id, body)
    except Phase4DError as e:
        raise HTTPException(404, str(e)) from e
    return {"id": str(row.id)}


@router.post("/match", status_code=201)
async def match(body: MatchRequest, s: S) -> dict[str, object]:
    try:
        row = await s.match(body)
    except Phase4DError as e:
        raise HTTPException(409, str(e)) from e
    if row is None:
        return {"proposal": False}
    return {
        "proposal": True,
        "id": str(row.id),
        "score": row.score,
        "confidence_band": row.confidence_band,
    }


@router.post("/merge-proposals", status_code=201)
async def merge(body: MergeProposalCreate, s: S) -> dict[str, str]:
    try:
        row = await s.create_merge_proposal(body)
    except Phase4DError as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(row.id), "status": row.status}


@router.post("/merge-proposals/{proposal_id}/approve")
async def approve(proposal_id: UUID, s: S) -> dict[str, str]:
    try:
        row = await s.approve(proposal_id)
    except Phase4DError as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(row.id), "status": row.status}


@router.post("/relationships", status_code=201)
async def relationship(body: RelationshipCreate, s: S) -> dict[str, str]:
    try:
        row = await s.create_relationship(body)
    except Phase4DError as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(row.id), "status": row.status}

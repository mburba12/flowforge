from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import Party
from .schemas import (
    OrganizationCreate,
    OrganizationUnitCreate,
    PartyRead,
    PersonCreate,
    SearchRequest,
)
from .service import PartyService

router = APIRouter(prefix="/api/v2", tags=["phase2a"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(p: P, db: D) -> PartyService:
    return PartyService(db, TenantContext(p.tenant_id, p.user_id))


@router.post("/organizations", response_model=PartyRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: OrganizationCreate, s: Annotated[PartyService, Depends(service)]
) -> Party:
    return await s.organization(body)


@router.post("/people", response_model=PartyRead, status_code=status.HTTP_201_CREATED)
async def create_person(body: PersonCreate, s: Annotated[PartyService, Depends(service)]) -> Party:
    return await s.person(body)


@router.get("/parties/{party_id}", response_model=PartyRead)
async def get_party(party_id: UUID, s: Annotated[PartyService, Depends(service)]) -> Party:
    party = await s.get(party_id)
    if party is None:
        raise HTTPException(404, "Party not found")
    return party


@router.post("/parties/search", response_model=list[PartyRead])
async def search_parties(body: SearchRequest, p: P, db: D) -> list[Party]:
    stmt = select(Party).where(Party.tenant_id == p.tenant_id)
    if body.status:
        stmt = stmt.where(Party.status == body.status)
    if body.query:
        stmt = stmt.where(Party.normalized_name.contains(body.query.lower()))
    return list((await db.scalars(stmt.offset(body.offset).limit(body.limit))).all())


@router.post("/organization-units", status_code=201)
async def create_unit(
    body: OrganizationUnitCreate, s: Annotated[PartyService, Depends(service)]
) -> dict[str, str]:
    u = await s.unit(body)
    return {"id": str(u.id), "code": u.code, "type": u.unit_type}

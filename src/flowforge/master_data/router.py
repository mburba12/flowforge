from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase2a.models import (
    Address,
    ContactMethod,
    ExternalReference,
    Identifier,
    OrganizationUnit,
    PartyRelationship,
    PartyRoleAssignment,
    PaymentTerm,
)

from .schemas import *  # noqa: F403, F405
from .service import MasterDataService

router = APIRouter(prefix="/api/v2/master-data", tags=["master-data"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D) -> MasterDataService:
    return MasterDataService(db, TenantContext(p.tenant_id, p.user_id))


def guard(fn) -> Any:
    async def wrapped(*args, **kwargs) -> Any:
        try:
            return await fn(*args, **kwargs)
        except LookupError as e:
            raise HTTPException(404, str(e)) from e
        except ValueError as e:
            raise HTTPException(409, str(e)) from e

    return wrapped


@router.post("/parties/{party_id}/contacts", status_code=201)
async def add_contact(
    party_id: UUID, body: ContactCreate, s: Annotated[MasterDataService, Depends(svc)]
):
    return await s.add_contact(party_id, body)


@router.get("/parties/{party_id}/contacts")
async def contacts(party_id: UUID, s: Annotated[MasterDataService, Depends(svc)]):
    await s.party(party_id)
    return await s.list_for(ContactMethod, ContactMethod.party_id, party_id)


@router.post("/parties/{party_id}/addresses", status_code=201)
async def add_address(
    party_id: UUID, body: AddressCreate, s: Annotated[MasterDataService, Depends(svc)]
):
    return await s.add_address(party_id, body)


@router.get("/parties/{party_id}/addresses")
async def addresses(party_id: UUID, s: Annotated[MasterDataService, Depends(svc)]):
    await s.party(party_id)
    return await s.list_for(Address, Address.party_id, party_id)


@router.post("/parties/{party_id}/identifiers", status_code=201)
async def add_identifier(
    party_id: UUID, body: IdentifierCreate, s: Annotated[MasterDataService, Depends(svc)]
):
    return await s.add_identifier(party_id, body)


@router.get("/parties/{party_id}/identifiers")
async def identifiers(party_id: UUID, s: Annotated[MasterDataService, Depends(svc)]):
    await s.party(party_id)
    items = await s.list_for(Identifier, Identifier.party_id, party_id)
    return [
        {
            "id": x.id,
            "identifier_type": x.identifier_type,
            "value": ("***" + x.value[-4:] if x.sensitive else x.value),
            "country_code": x.country_code,
            "sensitive": x.sensitive,
        }
        for x in items
    ]


@router.post("/parties/{party_id}/roles", status_code=201)
async def add_role(party_id: UUID, body: RoleCreate, s: Annotated[MasterDataService, Depends(svc)]):
    return await s.add_role(party_id, body)


@router.get("/parties/{party_id}/roles")
async def roles(party_id: UUID, s: Annotated[MasterDataService, Depends(svc)]):
    await s.party(party_id)
    return await s.list_for(PartyRoleAssignment, PartyRoleAssignment.party_id, party_id)


@router.post("/parties/{party_id}/relationships", status_code=201)
async def add_relationship(
    party_id: UUID, body: RelationshipCreate, s: Annotated[MasterDataService, Depends(svc)]
):
    return await s.add_relationship(party_id, body)


@router.get("/parties/{party_id}/relationships")
async def relationships(party_id: UUID, s: Annotated[MasterDataService, Depends(svc)]):
    await s.party(party_id)
    return await s.list_for(PartyRelationship, PartyRelationship.source_party_id, party_id)


@router.post("/parties/{party_id}/external-references", status_code=201)
async def add_reference(
    party_id: UUID, body: ExternalReferenceCreate, s: Annotated[MasterDataService, Depends(svc)]
):
    return await s.add_reference(party_id, body)


@router.get("/parties/{party_id}/external-references")
async def references(party_id: UUID, s: Annotated[MasterDataService, Depends(svc)]):
    await s.party(party_id)
    return await s.list_for(ExternalReference, ExternalReference.party_id, party_id)


@router.post("/payment-terms", status_code=201)
async def create_term(body: PaymentTermCreate, s: Annotated[MasterDataService, Depends(svc)]):
    return await s.create_term(body)


@router.get("/payment-terms")
async def terms(s: Annotated[MasterDataService, Depends(svc)]):
    return await s.list_for(PaymentTerm)


@router.get("/organization-units")
async def units(s: Annotated[MasterDataService, Depends(svc)]):
    return await s.list_for(OrganizationUnit)


@router.post("/parties/{party_id}/duplicate-candidates", status_code=201)
async def duplicate(
    party_id: UUID, body: DuplicateCreate, s: Annotated[MasterDataService, Depends(svc)]
):
    return await s.duplicate(party_id, body)


@router.post("/parties/{party_id}/merge", status_code=201)
async def merge(party_id: UUID, body: MergeRequest, s: Annotated[MasterDataService, Depends(svc)]):
    return await s.merge(party_id, body)

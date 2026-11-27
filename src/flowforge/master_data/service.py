from __future__ import annotations

from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase2a.models import (
    Address,
    ContactMethod,
    DuplicateCandidate,
    ExternalReference,
    Identifier,
    MergeHistory,
    Party,
    PartyRelationship,
    PartyRoleAssignment,
    PaymentTerm,
)
from flowforge.platform.services import record_change

from .schemas import (
    AddressCreate,
    ContactCreate,
    DuplicateCreate,
    ExternalReferenceCreate,
    IdentifierCreate,
    MergeRequest,
    PaymentTermCreate,
    RelationshipCreate,
    RoleCreate,
)

M = TypeVar("M")


class MasterDataService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def party(self, pid: UUID) -> Party:
        obj = await self.db.scalar(
            select(Party).where(Party.id == pid, Party.tenant_id == self.ctx.tenant_id)
        )
        if obj is None:
            raise LookupError("Party not found")
        return obj

    async def _save(self, obj: M, action: str, entity: str) -> M:
        self.db.add(obj)
        await self.db.flush()
        await record_change(
            self.db,
            self.ctx.tenant_id,
            self.ctx.user_id,
            action,
            entity,
            str(getattr(obj, "id", getattr(obj, "party_id", ""))),
        )
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def add_contact(self, pid: UUID, data: ContactCreate) -> ContactMethod:
        await self.party(pid)
        v = data.value.strip()
        n = v.lower()
        if data.is_primary:
            await self.db.execute(
                update(ContactMethod)
                .where(
                    ContactMethod.tenant_id == self.ctx.tenant_id,
                    ContactMethod.party_id == pid,
                    ContactMethod.contact_type == data.contact_type,
                )
                .values(is_primary=False)
            )
        return await self._save(
            ContactMethod(
                tenant_id=self.ctx.tenant_id, party_id=pid, normalized_value=n, **data.model_dump()
            ),
            "created",
            "party_contact",
        )

    async def add_address(self, pid: UUID, data: AddressCreate) -> Address:
        await self.party(pid)
        if data.is_primary:
            await self.db.execute(
                update(Address)
                .where(
                    Address.tenant_id == self.ctx.tenant_id,
                    Address.party_id == pid,
                    Address.address_type == data.address_type,
                )
                .values(is_primary=False)
            )
        return await self._save(
            Address(tenant_id=self.ctx.tenant_id, party_id=pid, **data.model_dump()),
            "created",
            "party_address",
        )

    async def add_identifier(self, pid: UUID, data: IdentifierCreate) -> Identifier:
        await self.party(pid)
        v = data.value.strip()
        return await self._save(
            Identifier(
                tenant_id=self.ctx.tenant_id,
                party_id=pid,
                normalized_value="".join(v.lower().split()),
                **data.model_dump(),
            ),
            "created",
            "party_identifier",
        )

    async def add_role(self, pid: UUID, data: RoleCreate) -> PartyRoleAssignment:
        await self.party(pid)
        return await self._save(
            PartyRoleAssignment(tenant_id=self.ctx.tenant_id, party_id=pid, **data.model_dump()),
            "created",
            "party_role",
        )

    async def add_relationship(self, pid: UUID, data: RelationshipCreate) -> PartyRelationship:
        await self.party(pid)
        await self.party(data.target_party_id)
        if pid == data.target_party_id:
            raise ValueError("A party cannot relate to itself")
        return await self._save(
            PartyRelationship(
                tenant_id=self.ctx.tenant_id, source_party_id=pid, **data.model_dump()
            ),
            "created",
            "party_relationship",
        )

    async def add_reference(self, pid: UUID, data: ExternalReferenceCreate) -> ExternalReference:
        await self.party(pid)
        return await self._save(
            ExternalReference(tenant_id=self.ctx.tenant_id, party_id=pid, **data.model_dump()),
            "created",
            "party_external_reference",
        )

    async def create_term(self, data: PaymentTermCreate) -> PaymentTerm:
        return await self._save(
            PaymentTerm(tenant_id=self.ctx.tenant_id, **data.model_dump()),
            "created",
            "payment_term",
        )

    async def duplicate(self, pid: UUID, data: DuplicateCreate) -> DuplicateCandidate:
        await self.party(pid)
        await self.party(data.right_party_id)
        if pid == data.right_party_id:
            raise ValueError("Duplicate parties must differ")
        return await self._save(
            DuplicateCandidate(
                tenant_id=self.ctx.tenant_id, left_party_id=pid, **data.model_dump()
            ),
            "created",
            "party_duplicate_candidate",
        )

    async def merge(self, source: UUID, data: MergeRequest) -> MergeHistory:
        s = await self.party(source)
        await self.party(data.target_party_id)
        if source == data.target_party_id:
            raise ValueError("Source and target must differ")
        if s.status == "merged":
            raise ValueError("Party already merged")
        s.status = "merged"
        s.merged_into_id = data.target_party_id
        h = MergeHistory(
            tenant_id=self.ctx.tenant_id,
            source_party_id=source,
            target_party_id=data.target_party_id,
            actor_user_id=self.ctx.user_id,
            reason=data.reason,
        )
        self.db.add(h)
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "merged", "party", str(source)
        )
        await self.db.commit()
        await self.db.refresh(h)
        return h

    async def list_for(
        self, model: type[M], party_column: Any | None = None, pid: UUID | None = None
    ) -> list[M]:
        stmt = select(model).where(model.tenant_id == self.ctx.tenant_id)
        if party_column is not None and pid is not None:
            stmt = stmt.where(party_column == pid)
        return list((await self.db.scalars(stmt)).all())

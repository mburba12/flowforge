from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.numbering import next_number
from flowforge.platform.services import record_change

from .enums import PartyKind, PartyStatus
from .models import Organization, OrganizationUnit, Party, PartyRoleAssignment, Person
from .normalization import normalize_name
from .schemas import OrganizationCreate, OrganizationUnitCreate, PersonCreate


class PartyService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def _number(self) -> str:
        return await next_number(self.db, self.ctx.tenant_id, "party")

    async def organization(self, data: OrganizationCreate) -> Party:
        p = Party(
            tenant_id=self.ctx.tenant_id,
            party_number=await self._number(),
            kind=PartyKind.ORGANIZATION,
            display_name=data.trade_name or data.legal_name,
            normalized_name=normalize_name(data.trade_name or data.legal_name),
        )
        self.db.add(p)
        await self.db.flush()
        self.db.add(
            Organization(
                party_id=p.id,
                tenant_id=self.ctx.tenant_id,
                legal_name=data.legal_name,
                trade_name=data.trade_name,
                registration_country=data.registration_country,
            )
        )
        for role in data.roles:
            self.db.add(PartyRoleAssignment(tenant_id=self.ctx.tenant_id, party_id=p.id, role=role))
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "created", "party", str(p.id)
        )
        await self.db.commit()
        await self.db.refresh(p)
        return p

    async def person(self, data: PersonCreate) -> Party:
        display = f"{data.given_name} {data.family_name}"
        p = Party(
            tenant_id=self.ctx.tenant_id,
            party_number=await self._number(),
            kind=PartyKind.PERSON,
            display_name=display,
            normalized_name=normalize_name(display),
        )
        self.db.add(p)
        await self.db.flush()
        self.db.add(
            Person(
                party_id=p.id,
                tenant_id=self.ctx.tenant_id,
                given_name=data.given_name,
                family_name=data.family_name,
                middle_name=data.middle_name,
                birth_date=data.birth_date,
            )
        )
        for role in data.roles:
            self.db.add(PartyRoleAssignment(tenant_id=self.ctx.tenant_id, party_id=p.id, role=role))
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "created", "party", str(p.id)
        )
        await self.db.commit()
        await self.db.refresh(p)
        return p

    async def get(self, party_id: UUID) -> Party | None:
        return await self.db.scalar(
            select(Party).where(Party.id == party_id, Party.tenant_id == self.ctx.tenant_id)
        )

    async def archive(self, party_id: UUID) -> Party | None:
        p = await self.get(party_id)
        if p:
            p.status = PartyStatus.ARCHIVED
            await record_change(
                self.db, self.ctx.tenant_id, self.ctx.user_id, "archived", "party", str(p.id)
            )
            await self.db.commit()
        return p

    async def unit(self, data: OrganizationUnitCreate) -> OrganizationUnit:
        if data.parent_id:
            parent = await self.db.scalar(
                select(OrganizationUnit).where(
                    OrganizationUnit.id == data.parent_id,
                    OrganizationUnit.tenant_id == self.ctx.tenant_id,
                )
            )
            if parent is None:
                raise ValueError("Parent unit not found")
        u = OrganizationUnit(tenant_id=self.ctx.tenant_id, **data.model_dump())
        self.db.add(u)
        await self.db.commit()
        await self.db.refresh(u)
        return u

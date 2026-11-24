from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class Party(Base):
    __tablename__ = "parties"
    __table_args__ = (
        UniqueConstraint("tenant_id", "party_number", name="uq_parties_tenant_number"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_number: Mapped[str] = mapped_column(String(50))
    kind: Mapped[str] = mapped_column(String(30), index=True)
    display_name: Mapped[str] = mapped_column(String(250), index=True)
    normalized_name: Mapped[str] = mapped_column(String(250), index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    merged_into_id: Mapped[UUID | None] = mapped_column(ForeignKey("parties.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Organization(Base):
    __tablename__ = "party_organizations"
    party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    legal_name: Mapped[str] = mapped_column(String(250))
    trade_name: Mapped[str | None] = mapped_column(String(250))
    registration_country: Mapped[str | None] = mapped_column(String(2))


class Person(Base):
    __tablename__ = "party_people"
    party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    given_name: Mapped[str] = mapped_column(String(120))
    family_name: Mapped[str] = mapped_column(String(120))
    middle_name: Mapped[str | None] = mapped_column(String(120))
    birth_date: Mapped[date | None] = mapped_column(Date)


class PartyRoleAssignment(Base):
    __tablename__ = "party_role_assignments"
    __table_args__ = (UniqueConstraint("tenant_id", "party_id", "role", name="uq_party_role"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class ContactMethod(Base):
    __tablename__ = "party_contact_methods"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    contact_type: Mapped[str] = mapped_column(String(30))
    value: Mapped[str] = mapped_column(String(320))
    normalized_value: Mapped[str] = mapped_column(String(320), index=True)
    label: Mapped[str | None] = mapped_column(String(100))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class Address(Base):
    __tablename__ = "party_addresses"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    address_type: Mapped[str] = mapped_column(String(30))
    line1: Mapped[str] = mapped_column(String(250))
    line2: Mapped[str | None] = mapped_column(String(250))
    city: Mapped[str] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    postal_code: Mapped[str] = mapped_column(String(30))
    country_code: Mapped[str] = mapped_column(String(2))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class Identifier(Base):
    __tablename__ = "party_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "identifier_type", "normalized_value", name="uq_party_identifier"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    identifier_type: Mapped[str] = mapped_column(String(80))
    value: Mapped[str] = mapped_column(String(250))
    normalized_value: Mapped[str] = mapped_column(String(250), index=True)
    country_code: Mapped[str | None] = mapped_column(String(2))
    sensitive: Mapped[bool] = mapped_column(Boolean, default=False)


class PartyRelationship(Base):
    __tablename__ = "party_relationships"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    source_party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"), index=True
    )
    target_party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"), index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class PaymentTerm(Base):
    __tablename__ = "payment_terms"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_payment_terms_code"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    due_days: Mapped[int] = mapped_column(Integer)
    discount_days: Mapped[int | None] = mapped_column(Integer)
    discount_basis_points: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ExternalReference(Base):
    __tablename__ = "party_external_references"
    __table_args__ = (
        UniqueConstraint("tenant_id", "system", "external_id", name="uq_external_reference"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    system: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(250))


class OrganizationUnit(Base):
    __tablename__ = "organization_units"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    unit_type: Mapped[str] = mapped_column(String(40))
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("organization_units.id"))
    party_id: Mapped[UUID | None] = mapped_column(ForeignKey("parties.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class DuplicateCandidate(Base):
    __tablename__ = "party_duplicate_candidates"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    left_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    right_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="open")
    reasons: Mapped[str] = mapped_column(Text, default="")


class MergeHistory(Base):
    __tablename__ = "party_merge_history"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    source_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id"))
    target_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id"))
    actor_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)
    merged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

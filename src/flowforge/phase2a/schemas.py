from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import AddressType, ContactType, PartyKind, PartyRole, RelationshipType


class OrganizationCreate(BaseModel):
    legal_name: str = Field(min_length=2, max_length=250)
    trade_name: str | None = None
    registration_country: str | None = Field(default=None, min_length=2, max_length=2)
    roles: set[PartyRole] = Field(default_factory=set)


class PersonCreate(BaseModel):
    given_name: str = Field(min_length=1, max_length=120)
    family_name: str = Field(min_length=1, max_length=120)
    middle_name: str | None = None
    birth_date: date | None = None
    roles: set[PartyRole] = Field(default_factory=set)


class PartyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    party_number: str
    kind: PartyKind
    display_name: str
    status: str


class ContactCreate(BaseModel):
    contact_type: ContactType
    value: str = Field(min_length=3, max_length=320)
    label: str | None = None
    is_primary: bool = False


class AddressCreate(BaseModel):
    address_type: AddressType
    line1: str
    line2: str | None = None
    city: str
    region: str | None = None
    postal_code: str
    country_code: str = Field(min_length=2, max_length=2)
    is_primary: bool = False


class IdentifierCreate(BaseModel):
    identifier_type: str
    value: str
    country_code: str | None = None
    sensitive: bool = False


class RelationshipCreate(BaseModel):
    target_party_id: UUID
    relationship_type: RelationshipType
    effective_from: date | None = None
    effective_to: date | None = None


class RoleCreate(BaseModel):
    role: PartyRole
    effective_from: date | None = None
    effective_to: date | None = None


class PaymentTermCreate(BaseModel):
    code: str
    name: str
    due_days: int = Field(ge=0, le=365)
    discount_days: int | None = Field(default=None, ge=0, le=365)
    discount_basis_points: int | None = Field(default=None, ge=0, le=10000)


class OrganizationUnitCreate(BaseModel):
    unit_type: str
    code: str
    name: str
    parent_id: UUID | None = None
    party_id: UUID | None = None


class MergeRequest(BaseModel):
    source_party_id: UUID
    target_party_id: UUID
    reason: str = Field(min_length=5, max_length=1000)

    @model_validator(mode="after")
    def distinct(self) -> "MergeRequest":
        if self.source_party_id == self.target_party_id:
            raise ValueError("Source and target must differ")
        return self


class SearchRequest(BaseModel):
    query: str = ""
    role: PartyRole | None = None
    status: str | None = "active"
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

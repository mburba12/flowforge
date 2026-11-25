from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=40)
    display_name: str = Field(min_length=1, max_length=240)
    legal_name: str | None = Field(default=None, max_length=300)


class ReferenceCreate(BaseModel):
    source_system: str
    source_table: str
    source_record_id: str
    external_identifier: str | None = None
    identity_fingerprint: str = Field(min_length=64, max_length=64)
    link_method: str
    link_confidence: int = Field(ge=0, le=100)


class MatchRequest(BaseModel):
    left_reference_id: UUID
    right_reference_id: UUID
    signals: dict[str, bool]


class MergeProposalCreate(BaseModel):
    target_entity_id: UUID
    member_entity_ids: list[UUID] = Field(min_length=2)
    idempotency_key: str = Field(min_length=8, max_length=100)


class MergeDecision(BaseModel):
    action: Literal["approve", "reject"]


class RelationshipCreate(BaseModel):
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str
    evidence: dict[str, object] = Field(default_factory=dict)

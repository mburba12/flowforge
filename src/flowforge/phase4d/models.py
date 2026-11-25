from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class CanonicalEntity(Base):
    __tablename__ = "canonical_entities"
    __table_args__ = (
        CheckConstraint("source_count >= 0", name="ck_canonical_entity_source_count"),
        CheckConstraint("canonical_version >= 1", name="ck_canonical_entity_version"),
        CheckConstraint(
            "confidence_band IN ('low','medium','high','verified')",
            name="ck_canonical_entity_confidence",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    display_name: Mapped[str] = mapped_column(String(240))
    normalized_name: Mapped[str] = mapped_column(String(240), index=True)
    legal_name: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(30), default="active")
    confidence_band: Mapped[str] = mapped_column(String(20), default="low")
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    canonical_version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ExternalEntityReference(Base):
    __tablename__ = "external_entity_references"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_system",
            "source_table",
            "source_record_id",
            name="uq_external_entity_source",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    canonical_entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_entities.id", ondelete="CASCADE"), index=True
    )
    source_system: Mapped[str] = mapped_column(String(100))
    source_table: Mapped[str] = mapped_column(String(120))
    source_record_id: Mapped[str] = mapped_column(String(180))
    external_identifier: Mapped[str | None] = mapped_column(String(255))
    identity_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    link_method: Mapped[str] = mapped_column(String(40))
    link_confidence: Mapped[int] = mapped_column(Integer)
    linked_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntityMatchCandidate(Base):
    __tablename__ = "entity_match_candidates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "left_reference_id",
            "right_reference_id",
            name="uq_entity_match_pair",
        ),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_entity_match_score"),
        CheckConstraint("left_reference_id <> right_reference_id", name="ck_entity_match_distinct"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    left_reference_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_entity_references.id", ondelete="CASCADE")
    )
    right_reference_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_entity_references.id", ondelete="CASCADE")
    )
    score: Mapped[int] = mapped_column(Integer)
    confidence_band: Mapped[str] = mapped_column(String(20))
    matching_signals: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntityMergeProposal(Base):
    __tablename__ = "entity_merge_proposals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_entity_merge_idempotency"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    target_entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_entities.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(30), default="draft")
    idempotency_key: Mapped[str] = mapped_column(String(100))
    conflict_summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    dry_run_result: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EntityMergeMember(Base):
    __tablename__ = "entity_merge_members"
    __table_args__ = (
        UniqueConstraint("tenant_id", "proposal_id", "entity_id", name="uq_entity_merge_member"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    proposal_id: Mapped[UUID] = mapped_column(
        ForeignKey("entity_merge_proposals.id", ondelete="CASCADE")
    )
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_entities.id", ondelete="CASCADE"))
    member_role: Mapped[str] = mapped_column(String(30))
    original_status: Mapped[str] = mapped_column(String(30))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntityMergeEvent(Base):
    __tablename__ = "entity_merge_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    proposal_id: Mapped[UUID] = mapped_column(
        ForeignKey("entity_merge_proposals.id", ondelete="CASCADE")
    )
    event_type: Mapped[str] = mapped_column(String(40))
    event_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CanonicalProduct(Base):
    __tablename__ = "canonical_products"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(240))
    normalized_name: Mapped[str] = mapped_column(String(240), index=True)
    product_type: Mapped[str] = mapped_column(String(40))
    parent_product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductSourceLink(Base):
    __tablename__ = "product_source_links"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "source_system", "source_record_id", name="uq_product_source"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    canonical_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="CASCADE")
    )
    source_system: Mapped[str] = mapped_column(String(100))
    source_record_id: Mapped[str] = mapped_column(String(180))
    provider_listing_id: Mapped[str | None] = mapped_column(String(180))
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SkuCrosswalk(Base):
    __tablename__ = "sku_crosswalks"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "identifier_type", "identifier_value", name="uq_sku_identifier"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    canonical_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="CASCADE")
    )
    identifier_type: Mapped[str] = mapped_column(String(20))
    identifier_value: Mapped[str] = mapped_column(String(180))
    unit_of_measure: Mapped[str] = mapped_column(String(30), default="each")
    conversion_numerator: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=1)
    conversion_denominator: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=1)
    status: Mapped[str] = mapped_column(String(30), default="active")


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_entity_id",
            "target_entity_id",
            "relationship_type",
            name="uq_entity_relationship",
        ),
        CheckConstraint(
            "source_entity_id <> target_entity_id",
            name="ck_entity_relationship_distinct",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    source_entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_entities.id", ondelete="CASCADE")
    )
    target_entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_entities.id", ondelete="CASCADE")
    )
    relationship_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="active")
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

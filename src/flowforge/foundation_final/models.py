from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class T:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )


class RequirementDependency(Base):
    __tablename__ = "foundation_requirement_dependencies"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    requirement_id: Mapped[str] = mapped_column(String(80))
    depends_on_id: Mapped[str] = mapped_column(String(80))
    __table_args__ = (
        UniqueConstraint("requirement_id", "depends_on_id", name="uq_requirement_dependency"),
    )


class ArtifactClassification(Base):
    __tablename__ = "foundation_artifact_classifications"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    artifact_path: Mapped[str] = mapped_column(String(500), unique=True)
    classification: Mapped[str] = mapped_column(String(40))
    requirement_id: Mapped[str | None] = mapped_column(String(80))
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)


class DelegatedAccess(T, Base):
    __tablename__ = "foundation_delegated_access"
    grantor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    delegate_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    scope_json: Mapped[str] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApprovalLimit(T, Base):
    __tablename__ = "foundation_approval_limits"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    permission_code: Mapped[str] = mapped_column(String(120))
    currency_code: Mapped[str] = mapped_column(String(3))
    limit_minor: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_id", "permission_code", "currency_code", name="uq_approval_limit"
        ),
    )


class SodRule(T, Base):
    __tablename__ = "foundation_sod_rules"
    code: Mapped[str] = mapped_column(String(80))
    permission_a: Mapped[str] = mapped_column(String(120))
    permission_b: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_sod_rule"),)


class ImportJob(T, Base):
    __tablename__ = "master_data_import_jobs"
    entity_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="uploaded")
    source_reference: Mapped[str] = mapped_column(String(500))
    mapping_json: Mapped[str] = mapped_column(Text, default="{}")
    errors_json: Mapped[str] = mapped_column(Text, default="[]")
    cursor: Mapped[str | None] = mapped_column(String(250))
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class LineageEdge(T, Base):
    __tablename__ = "master_data_lineage_edges"
    source_type: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[UUID]
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[UUID]
    relationship: Mapped[str] = mapped_column(String(80))
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_type",
            "source_id",
            "target_type",
            "target_id",
            "relationship",
            name="uq_lineage_edge",
        ),
    )


class SearchIndexItem(T, Base):
    __tablename__ = "master_data_search_index"
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[UUID]
    document_json: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    stale: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "entity_type", "entity_id", name="uq_search_index_entity"),
    )

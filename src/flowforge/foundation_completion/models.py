from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class T:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )


class ModuleEntitlement(T, Base):
    __tablename__ = "foundation_module_entitlements"
    module_code: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="enabled")
    dependencies_json: Mapped[str] = mapped_column(Text, default="[]")
    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("tenant_id", "module_code", name="uq_foundation_entitlement"),
    )


class AccessReview(T, Base):
    __tablename__ = "foundation_access_reviews"
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    scope_json: Mapped[str] = mapped_column(Text, default="{}")
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    decision_json: Mapped[str] = mapped_column(Text, default="{}")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupportGrant(T, Base):
    __tablename__ = "foundation_support_grants"
    support_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    scope_json: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class StewardshipTask(T, Base):
    __tablename__ = "master_data_stewardship_tasks"
    party_id: Mapped[UUID | None] = mapped_column(ForeignKey("parties.id"))
    task_type: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30), default="open")
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    priority: Mapped[int] = mapped_column(Integer, default=3)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    resolution: Mapped[str | None] = mapped_column(Text)


class DataQualityRule(T, Base):
    __tablename__ = "master_data_quality_rules"
    code: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(80))
    rule_type: Mapped[str] = mapped_column(String(40))
    configuration_json: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_mdq_rule"),)


class DataQualityIssue(T, Base):
    __tablename__ = "master_data_quality_issues"
    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("master_data_quality_rules.id", ondelete="CASCADE")
    )
    entity_id: Mapped[UUID]
    status: Mapped[str] = mapped_column(String(30), default="open")
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    resolved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class ExportJob(T, Base):
    __tablename__ = "master_data_export_jobs"
    job_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    cursor: Mapped[str | None] = mapped_column(String(250))
    format: Mapped[str] = mapped_column(String(20), default="jsonl")
    result_reference: Mapped[str | None] = mapped_column(String(500))
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class RequirementEvidence(Base):
    __tablename__ = "foundation_requirement_evidence"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    requirement_id: Mapped[str] = mapped_column(String(80))
    artifact_path: Mapped[str] = mapped_column(String(500))
    evidence_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    notes: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (
        UniqueConstraint(
            "requirement_id", "artifact_path", "evidence_type", name="uq_requirement_evidence"
        ),
    )

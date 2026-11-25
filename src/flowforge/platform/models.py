from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import AuditMixin, Base, IdMixin, TenantMixin


class Tenant(Base, IdMixin, AuditMixin):
    __tablename__ = "tenants"
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active")


class User(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "email",
            name="uq_users_tenant_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_users_tenant_id_id",
        ),
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Role(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_roles_tenant_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_roles_tenant_id_id",
        ),
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)


class Permission(Base, IdMixin):
    __tablename__ = "permissions"
    code: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class UserRole(Base, TenantMixin):
    __tablename__ = "user_roles"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_user_roles_tenant_user",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name="fk_user_roles_tenant_role",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "role_id",
            name=("uq_user_roles_tenant_user_role"),
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )


class RolePermission(Base, TenantMixin):
    __tablename__ = "role_permissions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name=("fk_role_permissions_tenant_role"),
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "role_id",
            "permission_id",
            name=("uq_role_permissions_tenant_role_permission"),
        ),
    )

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "permissions.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )


class AuditEntry(Base, IdMixin, TenantMixin):
    __tablename__ = "audit_entries"
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WorkflowDefinition(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "workflow_definitions"
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[int] = mapped_column(default=1)
    definition: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class WorkflowInstance(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "workflow_instances"
    definition_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_definitions.id"))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    context: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class DomainEvent(Base, IdMixin, TenantMixin):
    __tablename__ = "domain_events"
    event_type: Mapped[str] = mapped_column(String(150), index=True)
    aggregate_type: Mapped[str] = mapped_column(String(100))
    aggregate_id: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Document(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "documents"
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(150))
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)


class Notification(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "notifications"
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    channel: Mapped[str] = mapped_column(String(30), default="in_app")
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="queued")


class IntegrationConnection(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "integration_connections"
    provider: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="inactive")
    config: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class SearchDocument(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "search_documents"
    resource_type: Mapped[str] = mapped_column(String(100), index=True)
    resource_id: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)


class AnalyticsMetric(Base, IdMixin, TenantMixin, AuditMixin):
    __tablename__ = "analytics_metrics"
    code: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    value: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)

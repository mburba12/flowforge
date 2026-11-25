from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
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


class WorkforceConnection(Base):
    __tablename__ = "workforce_connections"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider",
            "external_organization_id",
            name="uq_workforce_connection",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(100))
    provider_family: Mapped[str] = mapped_column(String(60))
    external_organization_id: Mapped[str] = mapped_column(String(180))
    organization_name: Mapped[str] = mapped_column(String(240))
    credential_state: Mapped[str] = mapped_column(
        String(100), default="SANDBOX_CREDENTIAL_NOT_PERSISTED"
    )
    environment: Mapped[str] = mapped_column(String(20), default="sandbox")
    status: Mapped[str] = mapped_column(String(30), default="connected")
    cursor: Mapped[str | None] = mapped_column(String(500))
    connected_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkforceWorker(Base):
    __tablename__ = "workforce_workers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_worker_id",
            name="uq_workforce_worker",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("workforce_connections.id", ondelete="CASCADE")
    )
    external_worker_id: Mapped[str] = mapped_column(String(180))
    employee_number_mask: Mapped[str | None] = mapped_column(String(30))
    display_name: Mapped[str] = mapped_column(String(240))
    email_hash: Mapped[str | None] = mapped_column(String(64))
    worker_type: Mapped[str] = mapped_column(String(30))
    employment_status: Mapped[str] = mapped_column(String(40))
    hire_date: Mapped[date | None] = mapped_column(Date)
    termination_date: Mapped[date | None] = mapped_column(Date)
    tax_identifier_mask: Mapped[str | None] = mapped_column(String(20))
    bank_account_mask: Mapped[str | None] = mapped_column(String(20))


class WorkforceJob(Base):
    __tablename__ = "workforce_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "connection_id", "external_job_id", name="uq_workforce_job"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("workforce_connections.id", ondelete="CASCADE")
    )
    external_job_id: Mapped[str] = mapped_column(String(180))
    title: Mapped[str] = mapped_column(String(240))
    department: Mapped[str | None] = mapped_column(String(180))
    location: Mapped[str | None] = mapped_column(String(180))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkforceAssignment(Base):
    __tablename__ = "workforce_assignments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "worker_id",
            "external_assignment_id",
            name="uq_workforce_assignment",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("workforce_workers.id", ondelete="CASCADE"))
    job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workforce_jobs.id", ondelete="SET NULL")
    )
    external_assignment_id: Mapped[str] = mapped_column(String(180))
    pay_type: Mapped[str] = mapped_column(String(30))
    pay_rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    currency_code: Mapped[str | None] = mapped_column(String(3))
    effective_date: Mapped[date] = mapped_column(Date)


class PayrollRun(Base):
    __tablename__ = "workforce_payroll_runs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_payroll_run_id",
            name="uq_workforce_payroll_run",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("workforce_connections.id", ondelete="CASCADE")
    )
    external_payroll_run_id: Mapped[str] = mapped_column(String(180))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    pay_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(40))
    gross_pay: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    employee_taxes: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    employer_taxes: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    deductions: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    net_pay: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))


class PayrollLine(Base):
    __tablename__ = "workforce_payroll_lines"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "payroll_run_id",
            "external_line_id",
            name="uq_workforce_payroll_line",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("workforce_payroll_runs.id", ondelete="CASCADE")
    )
    worker_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workforce_workers.id", ondelete="SET NULL")
    )
    external_line_id: Mapped[str] = mapped_column(String(180))
    gross_pay: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    taxes: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    deductions: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    net_pay: Mapped[Decimal] = mapped_column(Numeric(20, 2))


class TimeEntry(Base):
    __tablename__ = "workforce_time_entries"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_time_entry_id",
            name="uq_workforce_time_entry",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("workforce_connections.id", ondelete="CASCADE")
    )
    worker_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workforce_workers.id", ondelete="SET NULL")
    )
    external_time_entry_id: Mapped[str] = mapped_column(String(180))
    work_date: Mapped[date] = mapped_column(Date)
    regular_minutes: Mapped[int] = mapped_column(Integer)
    overtime_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))


class BenefitEnrollment(Base):
    __tablename__ = "workforce_benefit_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_enrollment_id",
            name="uq_workforce_benefit_enrollment",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("workforce_connections.id", ondelete="CASCADE")
    )
    worker_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workforce_workers.id", ondelete="SET NULL")
    )
    external_enrollment_id: Mapped[str] = mapped_column(String(180))
    plan_type: Mapped[str] = mapped_column(String(60))
    plan_name: Mapped[str] = mapped_column(String(240))
    coverage_level: Mapped[str | None] = mapped_column(String(60))
    employee_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    employer_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(30))


class Candidate(Base):
    __tablename__ = "workforce_candidates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connection_id",
            "external_candidate_id",
            name="uq_workforce_candidate",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("workforce_connections.id", ondelete="CASCADE")
    )
    external_candidate_id: Mapped[str] = mapped_column(String(180))
    display_name: Mapped[str] = mapped_column(String(240))
    email_hash: Mapped[str | None] = mapped_column(String(64))
    stage: Mapped[str] = mapped_column(String(60))
    hired: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkforceSyncRun(Base):
    __tablename__ = "workforce_sync_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("workforce_connections.id", ondelete="CASCADE")
    )
    sync_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))
    workers_created: Mapped[int] = mapped_column(Integer, default=0)
    payroll_runs_created: Mapped[int] = mapped_column(Integer, default=0)
    time_entries_created: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkforceWebhookEvent(Base):
    __tablename__ = "workforce_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_workforce_webhook_event"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workforce_connections.id", ondelete="SET NULL")
    )
    provider: Mapped[str] = mapped_column(String(100))
    provider_event_id: Mapped[str] = mapped_column(String(180))
    event_type: Mapped[str] = mapped_column(String(100))
    signature_valid: Mapped[bool] = mapped_column(Boolean)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    payload_digest: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

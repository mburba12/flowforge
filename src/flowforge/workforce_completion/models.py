from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class T:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1)


class Assignment(T, Base):
    __tablename__ = "workforce_assignments_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    position_id: Mapped[UUID | None] = mapped_column(ForeignKey("workforce_positions_final.id"))
    manager_worker_id: Mapped[UUID | None] = mapped_column(ForeignKey("worker_profiles.id"))
    legal_entity_id: Mapped[UUID | None]
    organization_unit_id: Mapped[UUID | None] = mapped_column(ForeignKey("organization_units.id"))
    employment_type: Mapped[str] = mapped_column(String(40))
    effective_from: Mapped[date]
    effective_to: Mapped[date | None]
    status: Mapped[str] = mapped_column(String(30), default="active")


class Compensation(T, Base):
    __tablename__ = "workforce_compensation_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    effective_from: Mapped[date]
    effective_to: Mapped[date | None]
    pay_type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    frequency: Mapped[str] = mapped_column(String(30))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class Schedule(T, Base):
    __tablename__ = "workforce_schedules_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    work_date: Mapped[date]
    start_time: Mapped[time]
    end_time: Mapped[time]
    timezone: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    __table_args__ = (
        UniqueConstraint("tenant_id", "worker_id", "work_date", name="uq_worker_schedule_date"),
    )


class Timecard(T, Base):
    __tablename__ = "workforce_timecards_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    period_start: Mapped[date]
    period_end: Mapped[date]
    regular_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "worker_id", "period_start", "period_end", name="uq_worker_timecard_period"
        ),
    )


class LeavePolicy(T, Base):
    __tablename__ = "workforce_leave_policies_final"
    code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(20), default="hours")
    annual_entitlement: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    carryover_limit: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_leave_policy"),)


class LeaveRequest(T, Base):
    __tablename__ = "workforce_leave_requests_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    policy_id: Mapped[UUID] = mapped_column(ForeignKey("workforce_leave_policies_final.id"))
    starts_on: Mapped[date]
    ends_on: Mapped[date]
    units: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    reason: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class LifecycleTask(T, Base):
    __tablename__ = "workforce_lifecycle_tasks_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    lifecycle_type: Mapped[str] = mapped_column(String(30))
    task_code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(30), default="open")
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "worker_id", "lifecycle_type", "task_code", name="uq_worker_lifecycle_task"
        ),
    )


class RetirementPlan(T, Base):
    __tablename__ = "workforce_retirement_plans_final"
    code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(200))
    employee_max_bps: Mapped[int] = mapped_column(Integer, default=10000)
    employer_match_bps: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_retirement_plan"),)


class RetirementEnrollment(T, Base):
    __tablename__ = "workforce_retirement_enrollments_final"
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("workforce_retirement_plans_final.id"))
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    employee_bps: Mapped[int] = mapped_column(Integer)
    effective_date: Mapped[date]
    status: Mapped[str] = mapped_column(String(30), default="active")
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "plan_id", "worker_id", "effective_date", name="uq_retirement_enrollment"
        ),
    )


class WorkerDocument(T, Base):
    __tablename__ = "workforce_documents_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    document_type: Mapped[str] = mapped_column(String(80))
    storage_reference: Mapped[str] = mapped_column(String(500))
    classification: Mapped[str] = mapped_column(String(40), default="confidential")
    status: Mapped[str] = mapped_column(String(30), default="active")
    retention_until: Mapped[date | None]
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkforceExecution(T, Base):
    __tablename__ = "workforce_executions_final"
    operation: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(160))
    aggregate_type: Mapped[str] = mapped_column(String(60))
    aggregate_id: Mapped[UUID]
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    actor_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "operation", "idempotency_key", name="uq_workforce_execution"
        ),
    )

from datetime import date, datetime
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


class Position(T, Base):
    __tablename__ = "workforce_positions_final"
    code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(240))
    department_id: Mapped[UUID | None]
    status: Mapped[str] = mapped_column(String(30), default="open")
    headcount: Mapped[int] = mapped_column(Integer, default=1)
    filled: Mapped[int] = mapped_column(Integer, default=0)
    hiring_manager_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_workforce_position"),)


class Candidate(T, Base):
    __tablename__ = "workforce_candidates_final"
    candidate_number: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(240))
    email: Mapped[str] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="active")
    source: Mapped[str | None] = mapped_column(String(100))
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("tenant_id", "candidate_number", name="uq_candidate_number"),
    )


class Application(T, Base):
    __tablename__ = "workforce_applications_final"
    position_id: Mapped[UUID] = mapped_column(ForeignKey("workforce_positions_final.id"))
    candidate_id: Mapped[UUID] = mapped_column(ForeignKey("workforce_candidates_final.id"))
    stage: Mapped[str] = mapped_column(String(40), default="applied")
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("tenant_id", "position_id", "candidate_id", name="uq_position_candidate"),
    )


class Offer(T, Base):
    __tablename__ = "workforce_offers_final"
    application_id: Mapped[UUID] = mapped_column(ForeignKey("workforce_applications_final.id"))
    annual_compensation: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency_code: Mapped[str] = mapped_column(String(3))
    start_date: Mapped[date]
    status: Mapped[str] = mapped_column(String(30), default="draft")
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PerformanceReview(T, Base):
    __tablename__ = "workforce_reviews_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    period_start: Mapped[date]
    period_end: Mapped[date]
    status: Mapped[str] = mapped_column(String(30), default="draft")
    rating: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[str] = mapped_column(Text, default="")


class Goal(T, Base):
    __tablename__ = "workforce_goals_final"
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    title: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(30), default="active")
    target_date: Mapped[date | None]
    progress: Mapped[int] = mapped_column(Integer, default=0)


class Course(T, Base):
    __tablename__ = "workforce_courses_final"
    code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(300))
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    validity_days: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_workforce_course"),)


class Enrollment(T, Base):
    __tablename__ = "workforce_enrollments_final"
    course_id: Mapped[UUID] = mapped_column(ForeignKey("workforce_courses_final.id"))
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    status: Mapped[str] = mapped_column(String(30), default="assigned")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[int | None] = mapped_column(Integer)
    expires_on: Mapped[date | None]
    __table_args__ = (
        UniqueConstraint("tenant_id", "course_id", "worker_id", name="uq_course_worker"),
    )


class BenefitPlan(T, Base):
    __tablename__ = "workforce_benefit_plans_final"
    code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(240))
    plan_type: Mapped[str] = mapped_column(String(60))
    employee_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    employer_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_benefit_plan"),)


class BenefitEnrollment(T, Base):
    __tablename__ = "workforce_benefit_enrollments_final"
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("workforce_benefit_plans_final.id"))
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id"))
    effective_date: Mapped[date]
    end_date: Mapped[date | None]
    status: Mapped[str] = mapped_column(String(30), default="active")
    coverage_level: Mapped[str] = mapped_column(String(60))
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "plan_id", "worker_id", "effective_date", name="uq_benefit_enrollment"
        ),
    )


class WorkforceEvent(T, Base):
    __tablename__ = "workforce_events_outbox"
    event_type: Mapped[str] = mapped_column(String(100))
    aggregate_type: Mapped[str] = mapped_column(String(60))
    aggregate_id: Mapped[UUID]
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class WorkSchedule(Base):
    __tablename__ = "work_schedules"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    weekly_hours: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    schedule_id: Mapped[UUID] = mapped_column(ForeignKey("work_schedules.id"))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class TimeEntry(Base):
    __tablename__ = "time_entries"
    __table_args__ = (UniqueConstraint("tenant_id", "external_id", name="uq_time_external_id"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    work_location_id: Mapped[UUID] = mapped_column(ForeignKey("work_locations.id"))
    work_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    regular_hours: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    external_id: Mapped[str | None] = mapped_column(String(100))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LeaveType(Base):
    __tablename__ = "leave_types"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    leave_type_id: Mapped[UUID] = mapped_column(ForeignKey("leave_types.id"))
    available_hours: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    leave_type_id: Mapped[UUID] = mapped_column(ForeignKey("leave_types.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    requested_hours: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    status: Mapped[str] = mapped_column(String(30), default="submitted")
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class PayGroup(Base):
    __tablename__ = "pay_groups"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    pay_frequency: Mapped[str] = mapped_column(String(30))
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PayPeriod(Base):
    __tablename__ = "pay_periods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "pay_group_id", "period_code", name="uq_pay_period"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    pay_group_id: Mapped[UUID] = mapped_column(ForeignKey("pay_groups.id", ondelete="CASCADE"))
    period_code: Mapped[str] = mapped_column(String(30))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    pay_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="open")

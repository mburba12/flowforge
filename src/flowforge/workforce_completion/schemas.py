from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    worker_id: UUID
    position_id: UUID | None = None
    manager_worker_id: UUID | None = None
    legal_entity_id: UUID | None = None
    organization_unit_id: UUID | None = None
    employment_type: str
    effective_from: date
    effective_to: date | None = None


class CompensationCreate(BaseModel):
    worker_id: UUID
    effective_from: date
    effective_to: date | None = None
    pay_type: str = Field(pattern="^(salary|hourly|commission)$")
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    frequency: str


class ScheduleCreate(BaseModel):
    worker_id: UUID
    work_date: date
    start_time: time
    end_time: time
    timezone: str


class TimecardCreate(BaseModel):
    worker_id: UUID
    period_start: date
    period_end: date
    regular_hours: Decimal = Field(ge=0, le=744)
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0, le=744)


class LeavePolicyCreate(BaseModel):
    code: str
    name: str
    unit: str = "hours"
    annual_entitlement: Decimal = Field(ge=0)
    carryover_limit: Decimal = Field(default=Decimal("0"), ge=0)


class LeaveCreate(BaseModel):
    worker_id: UUID
    policy_id: UUID
    starts_on: date
    ends_on: date
    units: Decimal = Field(gt=0)
    reason: str | None = None


class LifecycleTaskCreate(BaseModel):
    worker_id: UUID
    lifecycle_type: str = Field(pattern="^(onboarding|offboarding)$")
    task_code: str
    title: str
    assigned_to: UUID | None = None
    due_at: datetime | None = None


class RetirementPlanCreate(BaseModel):
    code: str
    name: str
    employee_max_bps: int = Field(default=10000, ge=0, le=10000)
    employer_match_bps: int = Field(default=0, ge=0, le=10000)


class RetirementEnroll(BaseModel):
    plan_id: UUID
    worker_id: UUID
    employee_bps: int = Field(ge=0, le=10000)
    effective_date: date


class DocumentCreate(BaseModel):
    worker_id: UUID
    document_type: str
    storage_reference: str
    classification: str = "confidential"
    retention_until: date | None = None
    legal_hold: bool = False


class Action(BaseModel):
    target: str
    idempotency_key: str = Field(min_length=8)

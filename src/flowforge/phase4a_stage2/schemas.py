from datetime import date, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ScheduleCreate(BaseModel):
    code: str
    name: str
    weekly_hours: Decimal = Field(gt=0, le=168)


class TimeEntryCreate(BaseModel):
    worker_id: UUID
    work_location_id: UUID
    work_date: date
    start_time: time | None = None
    end_time: time | None = None
    regular_hours: Decimal = Field(default=Decimal("0"), ge=0, le=24)
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0, le=24)
    external_id: str | None = None

    @model_validator(mode="after")
    def valid_hours(self) -> "TimeEntryCreate":
        if self.regular_hours + self.overtime_hours > 24:
            raise ValueError("Daily hours cannot exceed 24")
        return self


class LeaveTypeCreate(BaseModel):
    code: str
    name: str
    paid: bool = False


class LeaveRequestCreate(BaseModel):
    worker_id: UUID
    leave_type_id: UUID
    start_date: date
    end_date: date
    requested_hours: Decimal = Field(gt=0)


class PayGroupCreate(BaseModel):
    code: str
    name: str
    pay_frequency: str
    currency_code: str = Field(min_length=3, max_length=3)


class PayPeriodCreate(BaseModel):
    pay_group_id: UUID
    period_code: str
    start_date: date
    end_date: date
    pay_date: date

    @model_validator(mode="after")
    def valid_dates(self) -> "PayPeriodCreate":
        if self.end_date < self.start_date:
            raise ValueError("Period end precedes start")
        if self.pay_date < self.end_date:
            raise ValueError("Pay date precedes period end")
        return self

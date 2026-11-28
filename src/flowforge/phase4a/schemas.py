from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from .enums import CompensationType, EmploymentStatus, PayFrequency, WorkerType


class WorkerCreate(BaseModel):
    party_id: UUID
    worker_type: WorkerType
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    hire_date: date
    legal_entity_id: UUID | None = None
    department_id: UUID | None = None
    location_id: UUID | None = None
    cost_center_id: UUID | None = None
    default_currency: str = Field(min_length=3, max_length=3)
    pay_frequency: PayFrequency


class WorkLocationCreate(BaseModel):
    code: str
    name: str
    country_code: str = Field(min_length=2, max_length=2)
    region_code: str | None = None
    locality: str | None = None


class AssignmentCreate(BaseModel):
    work_location_id: UUID
    effective_from: date
    effective_to: date | None = None


class CompensationCreate(BaseModel):
    compensation_type: CompensationType
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def valid_dates(self) -> "CompensationCreate":
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("Effective end precedes start")
        return self


class BankAccountCreate(BaseModel):
    account_token: str = Field(min_length=8, max_length=200)
    account_last4: str = Field(min_length=4, max_length=4)
    routing_token: str | None = Field(default=None, max_length=200)
    account_type: str


class TaxProfileCreate(BaseModel):
    residence_country: str = Field(min_length=2, max_length=2)
    residence_region: str | None = None
    filing_status: str
    additional_withholding: Decimal = Field(default=Decimal("0"), ge=0)
    effective_from: date
    effective_to: date | None = None


class BenefitPlanCreate(BaseModel):
    code: str
    name: str
    pretax: bool = True


class BenefitEnrollmentCreate(BaseModel):
    plan_id: UUID
    employee_amount: Decimal = Field(default=Decimal("0"), ge=0)
    employer_amount: Decimal = Field(default=Decimal("0"), ge=0)
    effective_from: date
    effective_to: date | None = None

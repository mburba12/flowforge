from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RetroCreate(BaseModel):
    worker_id: UUID
    source_run_id: UUID
    effective_date: date
    old_amount: Decimal
    new_amount: Decimal


class GarnishmentCreate(BaseModel):
    worker_id: UUID
    authority: str
    case_reference: str
    priority: int = Field(default=100, ge=1)
    amount_type: str = Field(pattern="^(fixed|percent)$")
    amount: Decimal = Field(gt=0)
    maximum_total: Decimal | None = Field(default=None, gt=0)


class BatchCreate(BaseModel):
    payroll_run_id: UUID
    batch_number: str
    payment_method: str = Field(pattern="^(ach|check|manual)$")


class BatchAction(BaseModel):
    target: str = Field(pattern="^(submitted|approved|simulated_released|voided)$")
    idempotency_key: str = Field(min_length=8)


class YearEndCreate(BaseModel):
    worker_id: UUID
    tax_year: int = Field(ge=2000, le=9999)
    form_type: str
    wages: Decimal = Field(ge=0)
    tax_withheld: Decimal = Field(ge=0)


class FilingSubmissionCreate(BaseModel):
    tax_return_id: UUID
    submission_key: str = Field(min_length=8)
    provider_code: str | None = None

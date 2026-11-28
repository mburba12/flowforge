from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AdjustmentCreate(BaseModel):
    worker_id: UUID
    payroll_run_id: UUID | None = None
    adjustment_type: str
    amount: Decimal
    taxable: bool = True
    reason: str = Field(min_length=3)


class Action(BaseModel):
    target: str
    idempotency_key: str = Field(min_length=8)


class ImportCreate(BaseModel):
    provider_code: str
    source_reference: str
    period_start: date
    period_end: date
    records: int = Field(ge=0)
    idempotency_key: str = Field(min_length=8)


class ParallelCreate(BaseModel):
    internal_run_id: UUID
    external_import_id: UUID
    gross_variance: Decimal
    tax_variance: Decimal
    net_variance: Decimal
    tolerance: Decimal = Field(default=Decimal("0"), ge=0)


class AmendmentCreate(BaseModel):
    tax_return_id: UUID
    reason: str = Field(min_length=3)
    original_total: Decimal
    amended_total: Decimal


class FilingArtifactCreate(BaseModel):
    tax_return_id: UUID
    artifact_type: str
    storage_reference: str
    checksum: str


class OffcycleCreate(BaseModel):
    pay_group_id: UUID
    pay_period_id: UUID
    ledger_id: UUID
    accounting_period_id: UUID
    idempotency_key: str = Field(min_length=8)

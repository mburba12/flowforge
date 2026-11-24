from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class JurisdictionCreate(BaseModel):
    code: str
    name: str
    level: str
    country_code: str = Field(min_length=2, max_length=2)
    parent_id: UUID | None = None


class TaxRuleCreate(BaseModel):
    jurisdiction_id: UUID
    code: str
    version: int = Field(default=1, ge=1)
    responsibility: str
    rate: Decimal = Field(ge=0, le=1)
    annual_wage_base: Decimal | None = Field(default=None, gt=0)
    effective_from: date
    effective_to: date | None = None


class TaxElectionCreate(BaseModel):
    worker_id: UUID
    jurisdiction_id: UUID
    filing_status: str
    additional_withholding: Decimal = Field(default=Decimal("0"), ge=0)
    exempt: bool = False
    effective_from: date
    effective_to: date | None = None


class TaxCalculate(BaseModel):
    payroll_worker_id: UUID
    tax_rule_id: UUID
    taxable_wages: Decimal = Field(ge=0)
    additional_withholding: Decimal = Field(default=Decimal("0"), ge=0)
    exempt: bool = False

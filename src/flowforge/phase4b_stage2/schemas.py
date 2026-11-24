from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class TaxLiabilityCreate(BaseModel):
    authority_id: UUID
    payroll_run_id: UUID
    liability_type: str
    amount: Decimal = Field(gt=0)
    due_date: date


class TaxReturnCreate(BaseModel):
    authority_id: UUID
    period_code: str
    period_start: date
    period_end: date
    due_date: date
    taxable_wages: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    tax_code: str

    @model_validator(mode="after")
    def valid_dates(self) -> "TaxReturnCreate":
        if self.period_end < self.period_start:
            raise ValueError("Period end precedes start")
        if self.due_date < self.period_end:
            raise ValueError("Due date precedes period end")
        return self


class TaxRemittanceCreate(BaseModel):
    liability_id: UUID
    payment_date: date
    amount: Decimal = Field(gt=0)
    ledger_id: UUID
    accounting_period_id: UUID
    tax_payable_account_id: UUID
    cash_account_id: UUID
    currency_code: str = Field(min_length=3, max_length=3)


class TaxNoticeCreate(BaseModel):
    authority_id: UUID
    notice_date: date
    reference: str
    amount: Decimal = Field(default=Decimal("0"), ge=0)

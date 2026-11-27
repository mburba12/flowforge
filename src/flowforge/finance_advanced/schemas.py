from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CloseRunCreate(BaseModel):
    ledger_id: UUID
    period_id: UUID
    tolerance: Decimal = Field(default=Decimal("0"), ge=0)


class RecurringJournalCreate(BaseModel):
    code: str
    description: str
    ledger_id: UUID
    frequency: str
    next_run_date: date
    debit_account_id: UUID
    credit_account_id: UUID
    amount: Decimal = Field(gt=0)


class PaymentBatchCreate(BaseModel):
    batch_number: str
    kind: str = Field(pattern="^(ap|refund|transfer)$")
    currency_code: str = Field(min_length=3, max_length=3)
    total_amount: Decimal = Field(ge=0)
    item_count: int = Field(ge=0)


class ReconciliationCreate(BaseModel):
    account_id: UUID | None = None
    source_name: str
    target_name: str
    source_balance: Decimal
    target_balance: Decimal
    tolerance: Decimal = Field(default=Decimal("0"), ge=0)
    evidence: str = ""


class BudgetVersionCreate(BaseModel):
    code: str
    name: str
    fiscal_year: int = Field(ge=1900, le=9999)


class BudgetLineCreate(BaseModel):
    account_id: UUID
    period_number: int = Field(ge=1, le=53)
    amount: Decimal
    dimension_json: str = "{}"


class ConsolidationCreate(BaseModel):
    code: str
    as_of_date: date
    source_entities: int = Field(ge=1)
    elimination_variance: Decimal = Decimal("0")


class AssetCreate(BaseModel):
    asset_number: str
    name: str
    acquisition_date: date
    cost: Decimal = Field(gt=0)
    salvage_value: Decimal = Field(default=Decimal("0"), ge=0)
    useful_life_periods: int = Field(gt=0)

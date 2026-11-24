from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from .enums import AccountType, NormalBalance


class CurrencyCreate(BaseModel):
    code: str = Field(min_length=3, max_length=3)
    name: str
    decimal_places: int = Field(default=2, ge=0, le=8)


class CalendarCreate(BaseModel):
    name: str
    start_month: int = Field(default=1, ge=1, le=12)


class PeriodCreate(BaseModel):
    calendar_id: UUID
    period_code: str
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def valid_dates(self) -> "PeriodCreate":
        if self.end_date < self.start_date:
            raise ValueError("End date precedes start date")
        return self


class LedgerCreate(BaseModel):
    code: str
    name: str
    base_currency: str = Field(min_length=3, max_length=3)


class AccountCreate(BaseModel):
    ledger_id: UUID
    account_code: str
    name: str
    account_type: AccountType
    normal_balance: NormalBalance
    parent_id: UUID | None = None
    posting_allowed: bool = True


class JournalLineCreate(BaseModel):
    account_id: UUID
    description: str | None = None
    debit: Decimal = Field(default=Decimal("0"), ge=0)
    credit: Decimal = Field(default=Decimal("0"), ge=0)
    currency_code: str = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def one_side(self) -> "JournalLineCreate":
        if (self.debit > 0) == (self.credit > 0):
            raise ValueError("Exactly one of debit or credit must be positive")
        return self


class JournalCreate(BaseModel):
    ledger_id: UUID
    period_id: UUID
    journal_date: date
    description: str
    lines: list[JournalLineCreate] = Field(min_length=2)

    @model_validator(mode="after")
    def balanced(self) -> "JournalCreate":
        debit = sum((line.debit for line in self.lines), Decimal("0"))
        credit = sum((line.credit for line in self.lines), Decimal("0"))
        if debit != credit:
            raise ValueError(f"Journal is unbalanced: debit={debit} credit={credit}")
        return self

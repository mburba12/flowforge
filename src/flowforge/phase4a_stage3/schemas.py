from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PayrollRunCreate(BaseModel):
    pay_group_id: UUID
    pay_period_id: UUID
    ledger_id: UUID
    accounting_period_id: UUID


class PayrollWorkerInput(BaseModel):
    worker_id: UUID
    regular_hours: Decimal = Field(default=Decimal("0"), ge=0)
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0)
    bonus: Decimal = Field(default=Decimal("0"), ge=0)
    pretax_deductions: Decimal = Field(default=Decimal("0"), ge=0)
    posttax_deductions: Decimal = Field(default=Decimal("0"), ge=0)
    employee_tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    employer_tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)


class PayrollCalculate(BaseModel):
    workers: list[PayrollWorkerInput] = Field(min_length=1)


class PayrollPostAccounts(BaseModel):
    wage_expense_account_id: UUID
    employer_tax_expense_account_id: UUID
    employee_tax_payable_account_id: UUID
    employer_tax_payable_account_id: UUID
    deductions_payable_account_id: UUID
    net_pay_payable_account_id: UUID
    currency_code: str = Field(min_length=3, max_length=3)


class PayrollPaymentCreate(BaseModel):
    worker_id: UUID
    cash_account_id: UUID
    net_pay_payable_account_id: UUID
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def accounts_differ(self) -> "PayrollPaymentCreate":
        if self.cash_account_id == self.net_pay_payable_account_id:
            raise ValueError("Cash and net-pay accounts must differ")
        return self

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class VendorCreate(BaseModel):
    party_id: UUID
    default_currency: str = Field(min_length=3, max_length=3)
    payment_terms_id: UUID | None = None
    ap_account_id: UUID


class POLineCreate(BaseModel):
    description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    expense_account_id: UUID


class POCreate(BaseModel):
    vendor_id: UUID
    currency_code: str = Field(min_length=3, max_length=3)
    order_date: date
    lines: list[POLineCreate] = Field(min_length=1)


class ReceiptLineCreate(BaseModel):
    po_line_id: UUID
    quantity: Decimal = Field(gt=0)


class ReceiptCreate(BaseModel):
    purchase_order_id: UUID
    receipt_date: date
    lines: list[ReceiptLineCreate] = Field(min_length=1)


class InvoiceLineCreate(BaseModel):
    po_line_id: UUID | None = None
    description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    account_id: UUID


class InvoiceCreate(BaseModel):
    vendor_id: UUID
    purchase_order_id: UUID | None = None
    invoice_number: str
    invoice_date: date
    due_date: date
    currency_code: str = Field(min_length=3, max_length=3)
    lines: list[InvoiceLineCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_due_date(self) -> "InvoiceCreate":
        if self.due_date < self.invoice_date:
            raise ValueError("Due date precedes invoice date")
        return self

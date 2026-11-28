from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    party_id: UUID
    default_currency: str = Field(min_length=3, max_length=3)
    ar_account_id: UUID
    revenue_account_id: UUID
    credit_limit: Decimal = Field(ge=0)


class ProductCreate(BaseModel):
    sku: str
    name: str
    base_uom: str
    sales_price: Decimal = Field(ge=0)
    standard_cost: Decimal = Field(ge=0)
    inventory_account_id: UUID
    cogs_account_id: UUID


class WarehouseCreate(BaseModel):
    code: str
    name: str


class LocationCreate(BaseModel):
    warehouse_id: UUID
    code: str
    location_type: str = "standard"


class InventoryAccounting(BaseModel):
    """GL posting for an inventory adjustment (inventory vs. offset account)."""

    ledger_id: UUID
    period_id: UUID
    offset_account_id: UUID
    adjustment_date: date
    currency_code: str = Field(default="USD", min_length=3, max_length=3)


class InventoryAdjust(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    location_id: UUID
    quantity: Decimal
    unit_cost: Decimal = Field(ge=0)
    idempotency_key: str
    accounting: InventoryAccounting | None = None


class OrderLineCreate(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class OrderCreate(BaseModel):
    customer_id: UUID
    ledger_id: UUID
    period_id: UUID
    order_date: date
    lines: list[OrderLineCreate] = Field(min_length=1)


class ReceiptCreate(BaseModel):
    open_item_id: UUID
    amount: Decimal = Field(gt=0)
    receipt_date: date
    cash_account_id: UUID
    ar_account_id: UUID
    ledger_id: UUID
    period_id: UUID
    currency_code: str = Field(min_length=3, max_length=3)

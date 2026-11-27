from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class RequisitionLineCreate(BaseModel):
    product_id: UUID | None = None
    description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class RequisitionCreate(BaseModel):
    number: str
    needed_on: date | None = None
    lines: list[RequisitionLineCreate] = Field(min_length=1)


class TransferCreate(BaseModel):
    number: str
    product_id: UUID
    source_warehouse_id: UUID
    target_warehouse_id: UUID
    quantity: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def different(self):
        if self.source_warehouse_id == self.target_warehouse_id:
            raise ValueError("Warehouses must differ")
        return self


class CountCreate(BaseModel):
    number: str
    warehouse_id: UUID


class CountLineCreate(BaseModel):
    product_id: UUID
    location_id: UUID | None = None
    system_quantity: Decimal
    counted_quantity: Decimal


class ReturnCreate(BaseModel):
    number: str
    order_id: UUID
    reason: str
    refund_amount: Decimal = Field(default=0, ge=0)


class RateCreate(BaseModel):
    shipment_reference: str
    carrier_code: str
    service_code: str
    amount: Decimal = Field(ge=0)
    currency_code: str = Field(min_length=3, max_length=3)
    estimated_days: int | None = Field(default=None, ge=0)


class LabelCreate(BaseModel):
    shipment_id: UUID
    carrier_code: str
    service_code: str
    idempotency_key: str = Field(min_length=8)


class TrackingCreate(BaseModel):
    shipment_id: UUID
    event_code: str
    description: str
    occurred_at: datetime
    location_text: str | None = None


class ClaimCreate(BaseModel):
    shipment_id: UUID
    claim_number: str
    reason: str
    amount: Decimal = Field(ge=0)
    evidence: dict = {}


class Action(BaseModel):
    target: str
    idempotency_key: str = Field(min_length=8)

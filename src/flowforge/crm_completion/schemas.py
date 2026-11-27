from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PriceListCreate(BaseModel):
    code: str
    name: str
    currency_code: str = Field(min_length=3, max_length=3)
    customer_id: UUID | None = None


class PriceItemCreate(BaseModel):
    product_id: UUID
    min_quantity: Decimal = Field(default=1, gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_bps: int = Field(default=0, ge=0, le=10000)


class PriceRequest(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    customer_id: UUID | None = None
    currency_code: str = Field(min_length=3, max_length=3)


class CampaignMemberCreate(BaseModel):
    party_id: UUID | None = None
    lead_id: UUID | None = None


class QuoteRevise(BaseModel):
    reason: str = Field(min_length=3)
    idempotency_key: str = Field(min_length=8)


class PortalUserCreate(BaseModel):
    party_id: UUID
    contact_party_id: UUID
    email: str
    role: str = Field(pattern="^(viewer|buyer|admin)$")


class IdempotentAction(BaseModel):
    idempotency_key: str = Field(min_length=8)
    reason: str | None = None


class SearchRequest(BaseModel):
    query: str = ""
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

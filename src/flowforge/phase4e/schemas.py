from decimal import Decimal

from pydantic import BaseModel, Field


class AmountReconciliationRequest(BaseModel):
    expected: Decimal
    actual: Decimal
    tolerance: Decimal = Field(ge=0)
    evidence: list[str] = Field(min_length=2)


class CommerceToCashRequest(BaseModel):
    order_total: Decimal
    captured: Decimal
    settled: Decimal
    deposited: Decimal
    tolerance: Decimal = Field(ge=0)

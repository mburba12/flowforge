from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CloseAssessmentRequest(BaseModel):
    ledger_id: UUID
    period_id: UUID
    tolerance: Decimal = Field(default=Decimal("0"), ge=0)


class ReconciliationAssessmentRequest(BaseModel):
    source_balance: Decimal
    target_balance: Decimal
    tolerance: Decimal = Field(default=Decimal("0"), ge=0)
    source_name: str = "source"
    target_name: str = "target"


class WorkflowResult(BaseModel):
    workflow: str
    ready: bool
    blockers: list[str]
    metrics: dict[str, object]

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RecordCreate(BaseModel):
    record_type: str = Field(
        pattern="^(item_revision|engineering_change|bom|routing|work_center|plan|mrp_run|schedule|work_order|material_issue|labor|wip|production_receipt|scrap|rework|costing|variance|inspection|nonconformance|material_review|capa|complaint|supplier_quality|audit|risk|validation|device_record|recall)$"
    )
    code: str
    payload: dict[str, Any] = {}
    parent_id: UUID | None = None


class Transition(BaseModel):
    target: str
    reason: str | None = None


class GenealogyCreate(BaseModel):
    parent_lot: str
    child_lot: str
    work_order_code: str
    payload: dict[str, Any] = {}

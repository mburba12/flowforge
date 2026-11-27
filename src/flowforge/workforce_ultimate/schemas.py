from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class InterviewCreate(BaseModel):
    application_id: UUID
    scheduled_at: datetime
    panel_ids: list[UUID] = Field(min_length=1)


class InterviewFeedback(BaseModel):
    scores: dict[str, int]
    notes: str = ""


class TemplateCreate(BaseModel):
    code: str
    name: str
    items: list[dict[str, Any]] = Field(min_length=1)


class DependentCreate(BaseModel):
    worker_id: UUID
    name: str
    relationship: str
    identifier: str | None = None


class ClockCreate(BaseModel):
    worker_id: UUID
    event_type: str = Field(pattern="^(clock_in|clock_out|break_start|break_end)$")
    occurred_at: datetime
    timezone: str
    source: str = "manual"
    idempotency_key: str = Field(min_length=8)


class TransferCreate(BaseModel):
    worker_id: UUID
    source_type: str
    source_id: UUID
    idempotency_key: str = Field(min_length=8)
    payload: dict[str, Any]


class ReportRequest(BaseModel):
    report_code: str
    parameters: dict[str, Any] = {}

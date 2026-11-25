from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class RecordCreate(BaseModel):
    status: str = "draft"
    code: str | None = Field(default=None, max_length=160)
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

class RecordUpdate(BaseModel):
    status: str | None = None
    code: str | None = Field(default=None, max_length=160)
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    data: dict[str, Any] | None = None
    version: int = Field(ge=1)

class RecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    status: str
    code: str | None
    name: str | None
    description: str | None
    data: dict[str, Any]
    version: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime

class ActionRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=255)
    record_id: UUID | None = None
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)

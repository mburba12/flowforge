from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9-]+$")


class TenantRead(TenantCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str


class BootstrapRequest(BaseModel):
    tenant: TenantCreate
    email: EmailStr
    password: str = Field(min_length=12)
    display_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    # Optional: without it the workspace is found from the email (and password).
    tenant_slug: str | None = None
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    """Public sign-up from the website: a new workspace and its owner."""

    organization: str = Field(min_length=2, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=12, max_length=200)
    plan: str | None = Field(default=None, max_length=40)


class SignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_slug: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    email: EmailStr
    display_name: str
    is_active: bool


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None


class WorkflowCreate(BaseModel):
    name: str
    definition: dict[str, object] = Field(default_factory=dict[str, Any])


class DocumentCreate(BaseModel):
    filename: str
    content_type: str
    storage_key: str
    metadata: dict[str, object] = Field(default_factory=dict[str, Any])


class NotificationCreate(BaseModel):
    subject: str
    body: str
    channel: str = "in_app"


class IntegrationCreate(BaseModel):
    provider: str
    name: str
    config: dict[str, object] = Field(default_factory=dict[str, Any])

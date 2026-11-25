from uuid import UUID

from pydantic import BaseModel, Field


class LinkSessionCreate(BaseModel):
    provider: str = "sandbox"


class TokenExchange(BaseModel):
    provider: str = "sandbox"
    public_token: str
    institution_id: str | None = None
    institution_name: str | None = None


class GLMappingCreate(BaseModel):
    gl_account_id: UUID
    mapping_type: str


class ManualTransactionCreate(BaseModel):
    connected_bank_account_id: UUID
    provider_transaction_id: str
    posted_at: str
    amount: str
    currency_code: str = Field(min_length=3, max_length=3)
    direction: str
    description: str

from pydantic import BaseModel


class FinanceConnectionCreate(BaseModel):
    provider: str
    authorization_code: str


class FinanceSyncRequest(BaseModel):
    sync_accounts: bool = True
    sync_documents: bool = True
    sync_expenses: bool = True


class FinanceWebhookIngest(BaseModel):
    provider_event_id: str
    event_type: str
    signature: str
    payload: str

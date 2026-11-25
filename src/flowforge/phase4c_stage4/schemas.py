from pydantic import BaseModel


class LogisticsConnectionCreate(BaseModel):
    provider: str
    authorization_code: str


class LogisticsSyncRequest(BaseModel):
    sync_tracking: bool = True
    sync_inventory: bool = True


class LogisticsWebhookIngest(BaseModel):
    provider_event_id: str
    event_type: str
    signature: str
    payload: str

from pydantic import BaseModel


class EngagementConnectionCreate(BaseModel):
    provider: str
    authorization_code: str


class EngagementSyncRequest(BaseModel):
    sync_contacts: bool = True
    sync_sales: bool = True
    sync_support: bool = True
    sync_marketing: bool = True


class EngagementWebhookIngest(BaseModel):
    provider_event_id: str
    event_type: str
    signature: str
    payload: str

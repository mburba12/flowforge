from pydantic import BaseModel


class CommerceConnectionCreate(BaseModel):
    provider: str
    authorization_code: str
    store_domain: str | None = None


class CommerceSyncRequest(BaseModel):
    sync_products: bool = True
    sync_orders: bool = True
    sync_customers: bool = True


class CommerceWebhookIngest(BaseModel):
    provider_event_id: str
    event_type: str
    signature: str
    payload: str

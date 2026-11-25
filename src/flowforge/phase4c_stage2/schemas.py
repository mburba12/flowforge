from pydantic import BaseModel


class PaymentConnectionCreate(BaseModel):
    provider: str
    authorization_code: str


class PaymentSyncRequest(BaseModel):
    include_payouts: bool = True


class WebhookIngest(BaseModel):
    provider_event_id: str
    event_type: str
    signature: str
    payload: str

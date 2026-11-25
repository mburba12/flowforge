from pydantic import BaseModel


class WorkforceConnectionCreate(BaseModel):
    provider: str
    authorization_code: str


class WorkforceSyncRequest(BaseModel):
    sync_workers: bool = True
    sync_payroll: bool = True
    sync_time: bool = True
    sync_benefits: bool = True


class WorkforceWebhookIngest(BaseModel):
    provider_event_id: str
    event_type: str
    signature: str
    payload: str

from pydantic import BaseModel,Field
from uuid import UUID
class ConnectionCreate(BaseModel):provider_type:str=Field(pattern="^(payment|banking|tax|payroll|commerce|shipping|identity|email|analytics|support)$");provider_code:str;mode:str=Field(default="sandbox",pattern="^(sandbox|production)$");configuration:dict={}
class OperationCreate(BaseModel):connection_id:UUID;operation:str;idempotency_key:str=Field(min_length=8);request:dict={}
class WebhookCreate(BaseModel):connection_id:UUID;event_id:str;signature_valid:bool;payload:dict
class StatusAction(BaseModel):target:str=Field(pattern="^(disabled|configured|sandbox_certified|production_approved|active|suspended)$")

from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class OpportunityTransition(BaseModel):stage:str=Field(pattern='^(qualification|discovery|proposal|negotiation|won|lost)$');probability:int=Field(ge=0,le=100);reason:str|None=None
class QuoteConvert(BaseModel):customer_id:UUID;ledger_id:UUID;period_id:UUID;order_date:date
class CreditExposure(BaseModel):delta:Decimal;reason:str
class PortalIssue(BaseModel):party_id:UUID;expires_in_minutes:int=Field(default=60,ge=5,le=10080)
class CampaignTransition(BaseModel):status:str=Field(pattern='^(draft|active|paused|completed|cancelled)$')

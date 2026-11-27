from datetime import date,datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field,model_validator
class LeadCreate(BaseModel):lead_number:str;company_name:str|None=None;contact_name:str;email:str|None=None;phone:str|None=None;source:str|None=None;owner_id:UUID|None=None;score:int=Field(default=0,ge=0,le=100)
class OpportunityCreate(BaseModel):opportunity_number:str;name:str;party_id:UUID|None=None;lead_id:UUID|None=None;amount:Decimal=Field(default=0,ge=0);currency_code:str=Field(default='USD',min_length=3,max_length=3);expected_close_date:date|None=None;owner_id:UUID|None=None
class ActivityCreate(BaseModel):entity_type:str;entity_id:UUID;activity_type:str;subject:str;notes:str='';due_at:datetime|None=None;owner_id:UUID|None=None
class CampaignCreate(BaseModel):code:str;name:str;starts_on:date|None=None;ends_on:date|None=None;budget:Decimal=Field(default=0,ge=0)
class QuoteLineCreate(BaseModel):product_id:UUID|None=None;description:str;quantity:Decimal=Field(gt=0);unit_price:Decimal=Field(ge=0);discount_bps:int=Field(default=0,ge=0,le=10000)
class QuoteCreate(BaseModel):quote_number:str;party_id:UUID;opportunity_id:UUID|None=None;currency_code:str=Field(default='USD',min_length=3,max_length=3);valid_until:date|None=None;lines:list[QuoteLineCreate]=Field(min_length=1)
class CreditCreate(BaseModel):party_id:UUID;credit_limit:Decimal=Field(ge=0);approved_by:UUID|None=None
class CommunicationCreate(BaseModel):party_id:UUID|None=None;channel:str;direction:str=Field(pattern='^(inbound|outbound)$');subject:str|None=None;body:str;external_reference:str|None=None
class Transition(BaseModel):target:str;reason:str|None=None

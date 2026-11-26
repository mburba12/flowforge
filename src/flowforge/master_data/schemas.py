from datetime import date
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field,model_validator
class ORMSchema(BaseModel):model_config=ConfigDict(from_attributes=True)
class ContactCreate(BaseModel):contact_type:str=Field(min_length=2,max_length=30);value:str=Field(min_length=2,max_length=320);label:str|None=None;is_primary:bool=False
class AddressCreate(BaseModel):address_type:str=Field(min_length=2,max_length=30);line1:str;line2:str|None=None;city:str;region:str|None=None;postal_code:str;country_code:str=Field(min_length=2,max_length=2);is_primary:bool=False
class IdentifierCreate(BaseModel):identifier_type:str;value:str=Field(min_length=2,max_length=250);country_code:str|None=None;sensitive:bool=True
class RoleCreate(BaseModel):role:str;effective_from:date|None=None;effective_to:date|None=None
class RelationshipCreate(BaseModel):
 target_party_id:UUID
 relationship_type:str
 effective_from:date|None=None
 effective_to:date|None=None
 @model_validator(mode='after')
 def valid_dates(self):
  if self.effective_from and self.effective_to and self.effective_to<self.effective_from:raise ValueError('effective_to precedes effective_from')
  return self
class PaymentTermCreate(BaseModel):code:str;name:str;due_days:int=Field(ge=0,le=3650);discount_days:int|None=Field(default=None,ge=0);discount_basis_points:int|None=Field(default=None,ge=0,le=10000);active:bool=True
class ExternalReferenceCreate(BaseModel):system:str;external_id:str
class DuplicateCreate(BaseModel):right_party_id:UUID;score:int=Field(ge=0,le=100);reasons:str=''
class DuplicateDecision(BaseModel):status:str=Field(pattern='^(confirmed|dismissed|merged)$')
class MergeRequest(BaseModel):target_party_id:UUID;reason:str=Field(min_length=3,max_length=2000)
class ItemRead(ORMSchema):id:UUID
class IdentifierRead(ORMSchema):id:UUID;identifier_type:str;value:str;country_code:str|None;sensitive:bool

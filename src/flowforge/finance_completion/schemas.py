from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class ExecuteRequest(BaseModel):idempotency_key:str=Field(min_length=8,max_length=160)
class AccrualCreate(BaseModel):code:str;ledger_id:UUID;debit_account_id:UUID;credit_account_id:UUID;amount:Decimal=Field(gt=0)
class AllocationCreate(BaseModel):code:str;source_account_id:UUID;target_json:str
class PaymentItemCreate(BaseModel):source_type:str;source_id:UUID;amount:Decimal=Field(gt=0)
class ReconciliationItemCreate(BaseModel):source_reference:str;target_reference:str|None=None;amount:Decimal
class MatchRequest(BaseModel):item_ids:list[UUID]=Field(min_length=1);target_reference:str
class StatementRequest(BaseModel):ledger_id:UUID;period_id:UUID

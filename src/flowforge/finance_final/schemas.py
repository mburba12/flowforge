from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class Execute(BaseModel):idempotency_key:str=Field(min_length=8,max_length=160);journal_date:date;period_id:UUID
class AllocationTarget(BaseModel):account_id:UUID;basis_points:int=Field(gt=0,le=10000)
class AllocationExecute(Execute):source_account_id:UUID;amount:Decimal=Field(gt=0);targets:list[AllocationTarget]=Field(min_length=1)
class PaymentAction(BaseModel):idempotency_key:str=Field(min_length=8);period_id:UUID;journal_date:date;cash_account_id:UUID;offset_account_id:UUID
class MatchAction(BaseModel):item_ids:list[UUID]=Field(min_length=1);target_reference:str
class Consolidate(BaseModel):idempotency_key:str=Field(min_length=8);ledger_id:UUID;period_id:UUID;journal_date:date;elimination_account_id:UUID;offset_account_id:UUID;amount:Decimal
class AssetPosting(BaseModel):idempotency_key:str=Field(min_length=8);ledger_id:UUID;period_id:UUID;journal_date:date;debit_account_id:UUID;credit_account_id:UUID;amount:Decimal=Field(gt=0);posting_type:str
class ReportRequest(BaseModel):ledger_id:UUID;period_id:UUID;comparison_period_id:UUID|None=None

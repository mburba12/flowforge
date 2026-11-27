from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class AmendmentCreate(BaseModel):amendment_type:str=Field(pattern='^(upgrade|downgrade|quantity|pause|resume|cancel)$');effective_date:date;new_quantity:Decimal=Field(gt=0)
class Idem(BaseModel):idempotency_key:str=Field(min_length=8)
class ProjectBillingCreate(BaseModel):project_id:UUID;period_start:date;period_end:date;idempotency_key:str=Field(min_length=8)
class AssetAccounting(BaseModel):ledger_id:UUID;period_id:UUID;debit_account_id:UUID;credit_account_id:UUID;transaction_date:date;amount:Decimal=Field(gt=0);idempotency_key:str=Field(min_length=8)

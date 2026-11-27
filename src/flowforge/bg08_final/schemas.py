from datetime import date,datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class PlanCreate(BaseModel):code:str;name:str;billing_interval:str=Field(pattern='^(monthly|quarterly|annual|usage)$');price:Decimal=Field(ge=0);currency_code:str=Field(min_length=3,max_length=3);trial_days:int=Field(default=0,ge=0)
class SubscriptionCreate(BaseModel):customer_id:UUID;plan_id:UUID;starts_on:date;quantity:Decimal=Field(default=1,gt=0)
class EntitlementCreate(BaseModel):code:str;limit_value:Decimal|None=Field(default=None,ge=0)
class UsageCreate(BaseModel):subscription_id:UUID;meter_code:str;quantity:Decimal=Field(gt=0);occurred_at:datetime;idempotency_key:str=Field(min_length=8)
class Action(BaseModel):target:str;reason:str|None=None
class BillingRunCreate(BaseModel):run_number:str;period_start:date;period_end:date
class ProjectCreate(BaseModel):code:str;name:str;customer_id:UUID|None=None;starts_on:date|None=None;ends_on:date|None=None;budget:Decimal=Field(default=0,ge=0);billing_method:str;manager_id:UUID|None=None
class TaskCreate(BaseModel):parent_id:UUID|None=None;code:str;name:str;budget_hours:Decimal=Field(default=0,ge=0);milestone:bool=False
class TimeCreate(BaseModel):task_id:UUID|None=None;worker_id:UUID;work_date:date;hours:Decimal=Field(gt=0,le=24);billable:bool=True;rate:Decimal=Field(default=0,ge=0)
class ExpenseCreate(BaseModel):worker_id:UUID|None=None;expense_date:date;description:str;amount:Decimal=Field(gt=0);billable:bool=True
class ChangeCreate(BaseModel):number:str;description:str;amount_change:Decimal;schedule_days:int=0
class BookCreate(BaseModel):asset_id:UUID;book_code:str;method:str=Field(pattern='^(straight_line|declining_balance|units)$');useful_life_periods:int=Field(gt=0);salvage_value:Decimal=Field(default=0,ge=0)
class AssetTxnCreate(BaseModel):asset_id:UUID;book_id:UUID|None=None;transaction_type:str=Field(pattern='^(capitalization|depreciation|transfer|impairment|disposal|maintenance)$');transaction_date:date;amount:Decimal;reason:str|None=None

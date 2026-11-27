from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class Idem(BaseModel):idempotency_key:str=Field(min_length=8)
class ConvertPO(Idem):vendor_id:UUID;currency_code:str=Field(min_length=3,max_length=3)
class Reserve(Idem):order_line_id:UUID;warehouse_id:UUID;quantity:Decimal=Field(gt=0)
class Fulfill(Idem):order_id:UUID;shipment_number:str;warehouse_id:UUID
class LandedCostCreate(BaseModel):receipt_id:UUID;cost_type:str;amount:Decimal=Field(gt=0);allocation_method:str=Field(pattern='^(value|quantity|weight|manual)$')
class ManifestCreate(BaseModel):manifest_number:str;carrier_code:str;shipment_ids:list[UUID]=Field(min_length=1)
class ClaimAction(BaseModel):target:str=Field(pattern='^(submitted|approved|rejected|paid|closed)$')
class ReturnReceive(Idem):warehouse_id:UUID

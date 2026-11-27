from datetime import datetime
from uuid import UUID
from pydantic import BaseModel,Field
class EntitlementCreate(BaseModel):module_code:str;dependencies:list[str]=[]
class AccessReviewCreate(BaseModel):name:str;reviewer_id:UUID;scope:dict={}
class SupportGrantCreate(BaseModel):support_user_id:UUID;scope:dict;reason:str=Field(min_length=8);expires_at:datetime;approved_by:UUID
class StewardshipCreate(BaseModel):party_id:UUID|None=None;task_type:str;assigned_to:UUID|None=None;priority:int=Field(default=3,ge=1,le=5);details:dict={}
class QualityRuleCreate(BaseModel):code:str;entity_type:str;rule_type:str;configuration:dict
class ExportCreate(BaseModel):job_type:str;format:str=Field(default='jsonl',pattern='^(jsonl|csv)$');cursor:str|None=None
class EvidenceCreate(BaseModel):requirement_id:str;artifact_path:str;evidence_type:str;status:str='pending';notes:str=''

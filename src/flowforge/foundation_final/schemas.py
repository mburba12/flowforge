from datetime import datetime
from uuid import UUID
from pydantic import BaseModel,Field
class DependencyCreate(BaseModel):requirement_id:str;depends_on_id:str
class ArtifactClassify(BaseModel):artifact_path:str;classification:str=Field(pattern='^(mapped|shared_foundation|obsolete|duplicate|generated|runtime_only|test_only)$');requirement_id:str|None=None
class DelegationCreate(BaseModel):grantor_id:UUID;delegate_id:UUID;scope:dict;starts_at:datetime;expires_at:datetime
class ApprovalLimitCreate(BaseModel):user_id:UUID;permission_code:str;currency_code:str=Field(min_length=3,max_length=3);limit_minor:int=Field(ge=0)
class SodCreate(BaseModel):code:str;permission_a:str;permission_b:str
class ImportCreate(BaseModel):entity_type:str;source_reference:str;mapping:dict={}
class LineageCreate(BaseModel):source_type:str;source_id:UUID;target_type:str;target_id:UUID;relationship:str
class IndexCreate(BaseModel):entity_type:str;entity_id:UUID;document:dict
class Decision(BaseModel):decision:str=Field(pattern='^(approve|reject|remediate|complete|revoke|archive|reactivate|verify|deactivate)$');reason:str=Field(min_length=3)

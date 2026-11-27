from pydantic import BaseModel,Field
class InfoCreate(BaseModel):record_type:str=Field(pattern="^(metric|dashboard|report|schedule|export|semantic_model|search_document|customer_portal|supplier_portal|employee_portal|auditor_portal)$");code:str;payload:dict={};permission_code:str|None=None
class CopilotCreate(BaseModel):prompt:str;context:dict;response:dict;citations:list[dict]=[];risk:str=Field(pattern="^(low|medium|high)$");cost_micros:int=Field(default=0,ge=0)
class ProposalAction(BaseModel):target:str=Field(pattern="^(approved|rejected|executed|cancelled)$")

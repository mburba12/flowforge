from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field,model_validator
class PositionCreate(BaseModel):code:str;title:str;department_id:UUID|None=None;headcount:int=Field(default=1,gt=0);hiring_manager_id:UUID|None=None
class CandidateCreate(BaseModel):candidate_number:str;name:str;email:str;phone:str|None=None;source:str|None=None;consent:bool=False
class ApplicationCreate(BaseModel):position_id:UUID;candidate_id:UUID;owner_id:UUID|None=None
class StageAction(BaseModel):target:str;reason:str|None=None
class OfferCreate(BaseModel):application_id:UUID;annual_compensation:Decimal=Field(gt=0);currency_code:str=Field(min_length=3,max_length=3);start_date:date
class ReviewCreate(BaseModel):
 worker_id:UUID
 reviewer_id:UUID
 period_start:date
 period_end:date
 rating:int|None=Field(default=None,ge=1,le=5)
 comments:str=''
 @model_validator(mode='after')
 def dates(self):
  if self.period_end<self.period_start:raise ValueError('Invalid review period')
  return self
class GoalCreate(BaseModel):worker_id:UUID;title:str;target_date:date|None=None
class GoalProgress(BaseModel):progress:int=Field(ge=0,le=100)
class CourseCreate(BaseModel):code:str;title:str;required:bool=False;validity_days:int|None=Field(default=None,gt=0)
class EnrollmentCreate(BaseModel):course_id:UUID;worker_id:UUID
class BenefitPlanCreate(BaseModel):code:str;name:str;plan_type:str;employee_cost:Decimal=Field(default=0,ge=0);employer_cost:Decimal=Field(default=0,ge=0)
class BenefitEnroll(BaseModel):plan_id:UUID;worker_id:UUID;effective_date:date;end_date:date|None=None;coverage_level:str

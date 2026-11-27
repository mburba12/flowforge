from datetime import datetime
from uuid import UUID,uuid4
from sqlalchemy import Boolean,DateTime,ForeignKey,Integer,String,Text,UniqueConstraint,func
from sqlalchemy.orm import Mapped,mapped_column
from flowforge.db.base import Base
class T:
 id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4);tenant_id:Mapped[UUID]=mapped_column(ForeignKey('tenants.id',ondelete='CASCADE'),index=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
class Interview(T,Base):
 __tablename__='workforce_interviews_final';application_id:Mapped[UUID]=mapped_column(ForeignKey('workforce_applications_final.id'));scheduled_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));panel_json:Mapped[str]=mapped_column(Text,default='[]');scorecard_json:Mapped[str]=mapped_column(Text,default='{}');status:Mapped[str]=mapped_column(String(30),default='scheduled')
class OnboardingTemplate(T,Base):
 __tablename__='workforce_onboarding_templates_final';code:Mapped[str]=mapped_column(String(80));name:Mapped[str]=mapped_column(String(200));tasks_json:Mapped[str]=mapped_column(Text);active:Mapped[bool]=mapped_column(Boolean,default=True);__table_args__=(UniqueConstraint('tenant_id','code',name='uq_onboarding_template'),)
class ReviewTemplate(T,Base):
 __tablename__='workforce_review_templates_final';code:Mapped[str]=mapped_column(String(80));name:Mapped[str]=mapped_column(String(200));competencies_json:Mapped[str]=mapped_column(Text);active:Mapped[bool]=mapped_column(Boolean,default=True);__table_args__=(UniqueConstraint('tenant_id','code',name='uq_review_template'),)
class BenefitDependent(T,Base):
 __tablename__='workforce_benefit_dependents_final';worker_id:Mapped[UUID]=mapped_column(ForeignKey('worker_profiles.id'));name:Mapped[str]=mapped_column(String(240));relationship:Mapped[str]=mapped_column(String(60));encrypted_identifier:Mapped[str|None]=mapped_column(Text);active:Mapped[bool]=mapped_column(Boolean,default=True)
class TimeClockEvent(T,Base):
 __tablename__='workforce_clock_events_final';worker_id:Mapped[UUID]=mapped_column(ForeignKey('worker_profiles.id'));event_type:Mapped[str]=mapped_column(String(30));occurred_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));timezone:Mapped[str]=mapped_column(String(80));source:Mapped[str]=mapped_column(String(40));idempotency_key:Mapped[str]=mapped_column(String(160));__table_args__=(UniqueConstraint('tenant_id','idempotency_key',name='uq_clock_event_idem'),)
class PayrollTransfer(T,Base):
 __tablename__='workforce_payroll_transfers_final';worker_id:Mapped[UUID]=mapped_column(ForeignKey('worker_profiles.id'));source_type:Mapped[str]=mapped_column(String(40));source_id:Mapped[UUID];status:Mapped[str]=mapped_column(String(30),default='queued');idempotency_key:Mapped[str]=mapped_column(String(160));payload_json:Mapped[str]=mapped_column(Text);__table_args__=(UniqueConstraint('tenant_id','idempotency_key',name='uq_workforce_payroll_transfer'),)
class WorkforceReportRun(T,Base):
 __tablename__='workforce_report_runs_final';report_code:Mapped[str]=mapped_column(String(80));parameters_json:Mapped[str]=mapped_column(Text,default='{}');status:Mapped[str]=mapped_column(String(30),default='completed');result_json:Mapped[str]=mapped_column(Text,default='{}');requested_by:Mapped[UUID]=mapped_column(ForeignKey('users.id'))

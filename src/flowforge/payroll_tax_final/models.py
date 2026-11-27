from datetime import date,datetime
from decimal import Decimal
from uuid import UUID,uuid4
from sqlalchemy import Boolean,Date,DateTime,ForeignKey,Integer,Numeric,String,Text,UniqueConstraint,func
from sqlalchemy.orm import Mapped,mapped_column
from flowforge.db.base import Base
class T:
 id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4);tenant_id:Mapped[UUID]=mapped_column(ForeignKey('tenants.id',ondelete='CASCADE'),index=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now());version:Mapped[int]=mapped_column(Integer,default=1)
class PayrollAdjustment(T,Base):
 __tablename__='payroll_adjustments_final';worker_id:Mapped[UUID]=mapped_column(ForeignKey('worker_profiles.id'));payroll_run_id:Mapped[UUID|None]=mapped_column(ForeignKey('payroll_runs.id'));adjustment_type:Mapped[str]=mapped_column(String(50));amount:Mapped[Decimal]=mapped_column(Numeric(20,6));taxable:Mapped[bool]=mapped_column(Boolean,default=True);status:Mapped[str]=mapped_column(String(30),default='draft');reason:Mapped[str]=mapped_column(Text);approved_by:Mapped[UUID|None]=mapped_column(ForeignKey('users.id'))
class PayrollImport(T,Base):
 __tablename__='payroll_imports_final';provider_code:Mapped[str]=mapped_column(String(80));source_reference:Mapped[str]=mapped_column(String(500));status:Mapped[str]=mapped_column(String(30),default='uploaded');period_start:Mapped[date];period_end:Mapped[date];records:Mapped[int]=mapped_column(Integer,default=0);errors_json:Mapped[str]=mapped_column(Text,default='[]');idempotency_key:Mapped[str]=mapped_column(String(160));__table_args__=(UniqueConstraint('tenant_id','idempotency_key',name='uq_payroll_import_idem'),)
class ParallelPayrollRun(T,Base):
 __tablename__='payroll_parallel_runs_final';internal_run_id:Mapped[UUID]=mapped_column(ForeignKey('payroll_runs.id'));external_import_id:Mapped[UUID]=mapped_column(ForeignKey('payroll_imports_final.id'));gross_variance:Mapped[Decimal]=mapped_column(Numeric(20,6),default=0);tax_variance:Mapped[Decimal]=mapped_column(Numeric(20,6),default=0);net_variance:Mapped[Decimal]=mapped_column(Numeric(20,6),default=0);status:Mapped[str]=mapped_column(String(30),default='exception')
class TaxAmendment(T,Base):
 __tablename__='tax_amendments_final';tax_return_id:Mapped[UUID]=mapped_column(ForeignKey('tax_returns.id'));reason:Mapped[str]=mapped_column(Text);status:Mapped[str]=mapped_column(String(30),default='draft');original_total:Mapped[Decimal]=mapped_column(Numeric(20,6));amended_total:Mapped[Decimal]=mapped_column(Numeric(20,6));approved_by:Mapped[UUID|None]=mapped_column(ForeignKey('users.id'))
class FilingArtifact(T,Base):
 __tablename__='tax_filing_artifacts_final';tax_return_id:Mapped[UUID]=mapped_column(ForeignKey('tax_returns.id'));artifact_type:Mapped[str]=mapped_column(String(60));storage_reference:Mapped[str]=mapped_column(String(500));checksum:Mapped[str]=mapped_column(String(128));status:Mapped[str]=mapped_column(String(30),default='generated')
class PayrollExecution(T,Base):
 __tablename__='payroll_executions_final';operation:Mapped[str]=mapped_column(String(80));idempotency_key:Mapped[str]=mapped_column(String(160));aggregate_type:Mapped[str]=mapped_column(String(60));aggregate_id:Mapped[UUID];result_json:Mapped[str]=mapped_column(Text,default='{}');actor_user_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'));__table_args__=(UniqueConstraint('tenant_id','operation','idempotency_key',name='uq_payroll_execution'),)
class PayrollEvent(T,Base):
 __tablename__='payroll_events_outbox';event_type:Mapped[str]=mapped_column(String(100));aggregate_type:Mapped[str]=mapped_column(String(60));aggregate_id:Mapped[UUID];payload_json:Mapped[str]=mapped_column(Text);status:Mapped[str]=mapped_column(String(30),default='pending');attempts:Mapped[int]=mapped_column(Integer,default=0)

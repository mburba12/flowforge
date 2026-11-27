from datetime import datetime
from decimal import Decimal
from uuid import UUID,uuid4
from sqlalchemy import DateTime,ForeignKey,Numeric,String,Text,UniqueConstraint,func
from sqlalchemy.orm import Mapped,mapped_column
from flowforge.db.base import Base
class T:
 id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4);tenant_id:Mapped[UUID]=mapped_column(ForeignKey('tenants.id',ondelete='CASCADE'),index=True)
class FinanceExecution(T,Base):
 __tablename__='finance_executions';execution_type:Mapped[str]=mapped_column(String(40));source_id:Mapped[UUID];idempotency_key:Mapped[str]=mapped_column(String(160));status:Mapped[str]=mapped_column(String(30),default='started');result_json:Mapped[str]=mapped_column(Text,default='{}');actor_user_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'));created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now());__table_args__=(UniqueConstraint('tenant_id','execution_type','idempotency_key',name='uq_finance_execution_idem'),)
class AccrualDefinition(T,Base):
 __tablename__='finance_accrual_definitions';code:Mapped[str]=mapped_column(String(60));ledger_id:Mapped[UUID]=mapped_column(ForeignKey('ledgers.id'));debit_account_id:Mapped[UUID]=mapped_column(ForeignKey('accounts.id'));credit_account_id:Mapped[UUID]=mapped_column(ForeignKey('accounts.id'));amount:Mapped[Decimal]=mapped_column(Numeric(20,6));status:Mapped[str]=mapped_column(String(30),default='active');__table_args__=(UniqueConstraint('tenant_id','code',name='uq_accrual_code'),)
class AllocationDefinition(T,Base):
 __tablename__='finance_allocation_definitions';code:Mapped[str]=mapped_column(String(60));source_account_id:Mapped[UUID]=mapped_column(ForeignKey('accounts.id'));target_json:Mapped[str]=mapped_column(Text);status:Mapped[str]=mapped_column(String(30),default='active');__table_args__=(UniqueConstraint('tenant_id','code',name='uq_allocation_code'),)
class PaymentBatchItem(T,Base):
 __tablename__='finance_payment_batch_items';batch_id:Mapped[UUID]=mapped_column(ForeignKey('finance_payment_batches.id',ondelete='CASCADE'));source_type:Mapped[str]=mapped_column(String(30));source_id:Mapped[UUID];amount:Mapped[Decimal]=mapped_column(Numeric(20,6));status:Mapped[str]=mapped_column(String(30),default='pending');provider_reference:Mapped[str|None]=mapped_column(String(200));__table_args__=(UniqueConstraint('tenant_id','batch_id','source_type','source_id',name='uq_payment_item_source'),)
class ReconciliationItem(T,Base):
 __tablename__='finance_reconciliation_items';session_id:Mapped[UUID]=mapped_column(ForeignKey('finance_reconciliation_sessions.id',ondelete='CASCADE'));source_reference:Mapped[str]=mapped_column(String(200));target_reference:Mapped[str|None]=mapped_column(String(200));amount:Mapped[Decimal]=mapped_column(Numeric(20,6));status:Mapped[str]=mapped_column(String(30),default='unmatched');match_group:Mapped[UUID|None]

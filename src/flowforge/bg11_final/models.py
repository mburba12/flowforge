from datetime import datetime
from uuid import UUID,uuid4
from sqlalchemy import DateTime,ForeignKey,Integer,String,Text,UniqueConstraint,func
from sqlalchemy.orm import Mapped,mapped_column
from flowforge.db.base import Base
class T:
 id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
 tenant_id:Mapped[UUID]=mapped_column(ForeignKey("tenants.id",ondelete="CASCADE"),index=True)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
 version:Mapped[int]=mapped_column(Integer,default=1)

class ProviderConnection(T,Base):
 __tablename__="bg11_provider_connections"
 provider_type:Mapped[str]=mapped_column(String(60));provider_code:Mapped[str]=mapped_column(String(100));status:Mapped[str]=mapped_column(String(30),default="disabled");mode:Mapped[str]=mapped_column(String(20),default="sandbox");configuration_json:Mapped[str]=mapped_column(Text,default="{}");cursor:Mapped[str|None]=mapped_column(String(500));last_sync_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));__table_args__=(UniqueConstraint("tenant_id","provider_type","provider_code",name="uq_bg11_provider"),)
class ProviderOperation(T,Base):
 __tablename__="bg11_provider_operations"
 connection_id:Mapped[UUID]=mapped_column(ForeignKey("bg11_provider_connections.id",ondelete="CASCADE"));operation:Mapped[str]=mapped_column(String(100));idempotency_key:Mapped[str]=mapped_column(String(160));status:Mapped[str]=mapped_column(String(30),default="queued");request_json:Mapped[str]=mapped_column(Text);response_json:Mapped[str]=mapped_column(Text,default="{}");attempts:Mapped[int]=mapped_column(Integer,default=0);__table_args__=(UniqueConstraint("tenant_id","connection_id","idempotency_key",name="uq_bg11_operation"),)
class WebhookReceipt(T,Base):
 __tablename__="bg11_webhook_receipts"
 connection_id:Mapped[UUID]=mapped_column(ForeignKey("bg11_provider_connections.id",ondelete="CASCADE"));event_id:Mapped[str]=mapped_column(String(200));signature_valid:Mapped[int]=mapped_column(Integer,default=0);payload_json:Mapped[str]=mapped_column(Text);status:Mapped[str]=mapped_column(String(30),default="received");__table_args__=(UniqueConstraint("tenant_id","connection_id","event_id",name="uq_bg11_webhook"),)

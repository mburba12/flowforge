from datetime import datetime
from decimal import Decimal
from uuid import UUID,uuid4
from sqlalchemy import Boolean,DateTime,ForeignKey,Integer,Numeric,String,Text,UniqueConstraint,func
from sqlalchemy.orm import Mapped,mapped_column
from flowforge.db.base import Base
class T:
 id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4);tenant_id:Mapped[UUID]=mapped_column(ForeignKey('tenants.id',ondelete='CASCADE'),index=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now());version:Mapped[int]=mapped_column(Integer,default=1)
class PriceList(T,Base):
 __tablename__='crm_price_lists';code:Mapped[str]=mapped_column(String(80));name:Mapped[str]=mapped_column(String(200));currency_code:Mapped[str]=mapped_column(String(3));active:Mapped[bool]=mapped_column(Boolean,default=True);customer_id:Mapped[UUID|None]=mapped_column(ForeignKey('parties.id'));__table_args__=(UniqueConstraint('tenant_id','code',name='uq_crm_price_list'),)
class PriceListItem(T,Base):
 __tablename__='crm_price_list_items';price_list_id:Mapped[UUID]=mapped_column(ForeignKey('crm_price_lists.id',ondelete='CASCADE'));product_id:Mapped[UUID]=mapped_column(ForeignKey('products.id'));min_quantity:Mapped[Decimal]=mapped_column(Numeric(20,6),default=1);unit_price:Mapped[Decimal]=mapped_column(Numeric(20,6));discount_bps:Mapped[int]=mapped_column(Integer,default=0);__table_args__=(UniqueConstraint('tenant_id','price_list_id','product_id','min_quantity',name='uq_crm_price_tier'),)
class CampaignMember(T,Base):
 __tablename__='crm_campaign_members';campaign_id:Mapped[UUID]=mapped_column(ForeignKey('crm_campaigns_final.id',ondelete='CASCADE'));party_id:Mapped[UUID|None]=mapped_column(ForeignKey('parties.id'));lead_id:Mapped[UUID|None]=mapped_column(ForeignKey('crm_leads_final.id'));status:Mapped[str]=mapped_column(String(30),default='targeted');response:Mapped[str|None]=mapped_column(String(80));attributed_amount:Mapped[Decimal]=mapped_column(Numeric(20,6),default=0)
class QuoteRevision(T,Base):
 __tablename__='crm_quote_revisions';quote_id:Mapped[UUID]=mapped_column(ForeignKey('crm_quotes_final.id',ondelete='CASCADE'));revision_number:Mapped[int]=mapped_column(Integer);snapshot_json:Mapped[str]=mapped_column(Text);reason:Mapped[str]=mapped_column(Text);created_by:Mapped[UUID]=mapped_column(ForeignKey('users.id'));__table_args__=(UniqueConstraint('tenant_id','quote_id','revision_number',name='uq_crm_quote_revision'),)
class PortalUser(T,Base):
 __tablename__='crm_portal_users';party_id:Mapped[UUID]=mapped_column(ForeignKey('parties.id'));contact_party_id:Mapped[UUID]=mapped_column(ForeignKey('parties.id'));email:Mapped[str]=mapped_column(String(320));status:Mapped[str]=mapped_column(String(30),default='active');role:Mapped[str]=mapped_column(String(40),default='viewer');failed_attempts:Mapped[int]=mapped_column(Integer,default=0);__table_args__=(UniqueConstraint('tenant_id','email',name='uq_crm_portal_email'),)
class CRMExecution(T,Base):
 __tablename__='crm_executions';operation:Mapped[str]=mapped_column(String(60));idempotency_key:Mapped[str]=mapped_column(String(160));entity_type:Mapped[str]=mapped_column(String(60));entity_id:Mapped[UUID];result_json:Mapped[str]=mapped_column(Text,default='{}');actor_user_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'));__table_args__=(UniqueConstraint('tenant_id','operation','idempotency_key',name='uq_crm_execution'),)
class CRMEvent(T,Base):
 __tablename__='crm_events_outbox';event_type:Mapped[str]=mapped_column(String(100));aggregate_type:Mapped[str]=mapped_column(String(60));aggregate_id:Mapped[UUID];payload_json:Mapped[str]=mapped_column(Text);status:Mapped[str]=mapped_column(String(30),default='pending');attempts:Mapped[int]=mapped_column(Integer,default=0)

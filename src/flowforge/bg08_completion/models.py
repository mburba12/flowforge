from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.db.base import Base


class T:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SubscriptionAmendment(T, Base):
    __tablename__ = "billing_subscription_amendments_final"
    subscription_id: Mapped[UUID] = mapped_column(ForeignKey("billing_subscriptions_final.id"))
    amendment_type: Mapped[str] = mapped_column(String(40))
    effective_date: Mapped[date]
    old_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    new_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    proration_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class BillingRunItem(T, Base):
    __tablename__ = "billing_run_items_final"
    billing_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("billing_runs_final.id", ondelete="CASCADE")
    )
    subscription_id: Mapped[UUID] = mapped_column(ForeignKey("billing_subscriptions_final.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    status: Mapped[str] = mapped_column(String(30), default="calculated")
    invoice_id: Mapped[UUID | None] = mapped_column(ForeignKey("customer_invoices.id"))
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "billing_run_id", "subscription_id", name="uq_billing_run_subscription"
        ),
    )


class ProjectBilling(T, Base):
    __tablename__ = "project_billing_runs_final"
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects_final.id"))
    period_start: Mapped[date]
    period_end: Mapped[date]
    status: Mapped[str] = mapped_column(String(30), default="draft")
    billable_time: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    billable_expenses: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    invoice_id: Mapped[UUID | None] = mapped_column(ForeignKey("customer_invoices.id"))
    revenue_recognized: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)


class BG08Execution(T, Base):
    __tablename__ = "bg08_executions_final"
    operation: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(160))
    aggregate_type: Mapped[str] = mapped_column(String(60))
    aggregate_id: Mapped[UUID]
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    actor_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "operation", "idempotency_key", name="uq_bg08_execution"),
    )

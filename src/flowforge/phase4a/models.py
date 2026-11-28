from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.core.encrypted_types import EncryptedText
from flowforge.db.base import Base


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"
    __table_args__ = (UniqueConstraint("tenant_id", "worker_number", name="uq_worker_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id"), index=True)
    worker_number: Mapped[str] = mapped_column(String(50))
    worker_type: Mapped[str] = mapped_column(String(30))
    employment_status: Mapped[str] = mapped_column(String(30), default="pending")
    hire_date: Mapped[date] = mapped_column(Date)
    termination_date: Mapped[date | None] = mapped_column(Date)
    legal_entity_id: Mapped[UUID | None] = mapped_column(ForeignKey("organization_units.id"))
    department_id: Mapped[UUID | None] = mapped_column(ForeignKey("organization_units.id"))
    location_id: Mapped[UUID | None] = mapped_column(ForeignKey("organization_units.id"))
    cost_center_id: Mapped[UUID | None] = mapped_column(ForeignKey("organization_units.id"))
    default_currency: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    pay_frequency: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkLocation(Base):
    __tablename__ = "work_locations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    country_code: Mapped[str] = mapped_column(String(2))
    region_code: Mapped[str | None] = mapped_column(String(20))
    locality: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkerAssignment(Base):
    __tablename__ = "worker_assignments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    work_location_id: Mapped[UUID] = mapped_column(ForeignKey("work_locations.id"))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    primary: Mapped[bool] = mapped_column(Boolean, default=True)


class CompensationRate(Base):
    __tablename__ = "compensation_rates"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"), index=True
    )
    compensation_type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class WorkerBankAccount(Base):
    __tablename__ = "worker_bank_accounts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    # Bank account and routing numbers: encrypted at rest.
    account_token: Mapped[str] = mapped_column(
        EncryptedText("worker_bank_accounts.account_token", 500)
    )
    account_last4: Mapped[str] = mapped_column(String(4))
    routing_token: Mapped[str | None] = mapped_column(
        EncryptedText("worker_bank_accounts.routing_token", 500)
    )
    account_type: Mapped[str] = mapped_column(String(30))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkerTaxProfile(Base):
    __tablename__ = "worker_tax_profiles"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    residence_country: Mapped[str] = mapped_column(String(2))
    residence_region: Mapped[str | None] = mapped_column(String(20))
    filing_status: Mapped[str] = mapped_column(String(50))
    additional_withholding: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class BenefitPlan(Base):
    __tablename__ = "benefit_plans"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    pretax: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class BenefitEnrollment(Base):
    __tablename__ = "benefit_enrollments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("benefit_plans.id"))
    employee_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    employer_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)

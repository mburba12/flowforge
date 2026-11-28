from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.core.encrypted_types import EncryptedText
from flowforge.db.base import Base


class TaxJurisdiction(Base):
    __tablename__ = "tax_jurisdictions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    level: Mapped[str] = mapped_column(String(30))
    country_code: Mapped[str] = mapped_column(String(2))
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("tax_jurisdictions.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TaxAuthority(Base):
    __tablename__ = "tax_authorities"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    jurisdiction_id: Mapped[UUID] = mapped_column(ForeignKey("tax_jurisdictions.id"))
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))


class TaxRegistration(Base):
    __tablename__ = "tax_registrations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    authority_id: Mapped[UUID] = mapped_column(ForeignKey("tax_authorities.id"))
    # Tax registration number: encrypted at rest.
    registration_token: Mapped[str] = mapped_column(
        EncryptedText("tax_registrations.registration_token", 500)
    )
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class TaxRule(Base):
    __tablename__ = "tax_rules"
    __table_args__ = (UniqueConstraint("tenant_id", "code", "version", name="uq_tax_rule_version"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    jurisdiction_id: Mapped[UUID] = mapped_column(ForeignKey("tax_jurisdictions.id"))
    code: Mapped[str] = mapped_column(String(50))
    version: Mapped[int] = mapped_column(default=1)
    responsibility: Mapped[str] = mapped_column(String(20))
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 8))
    annual_wage_base: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="active")


class WorkerTaxElection(Base):
    __tablename__ = "worker_tax_elections"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    jurisdiction_id: Mapped[UUID] = mapped_column(ForeignKey("tax_jurisdictions.id"))
    filing_status: Mapped[str] = mapped_column(String(50))
    additional_withholding: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    exempt: Mapped[bool] = mapped_column(Boolean, default=False)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class PayrollTaxCalculation(Base):
    __tablename__ = "payroll_tax_calculations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    payroll_worker_id: Mapped[UUID] = mapped_column(
        ForeignKey("payroll_run_workers.id", ondelete="CASCADE")
    )
    tax_rule_id: Mapped[UUID] = mapped_column(ForeignKey("tax_rules.id"))
    taxable_wages: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    employee_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    employer_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    explanation: Mapped[str] = mapped_column(String(500))

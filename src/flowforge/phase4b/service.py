from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .calculator import calculate_tax
from .models import (
    PayrollTaxCalculation,
    TaxJurisdiction,
    TaxRule,
    WorkerTaxElection,
)
from .schemas import (
    JurisdictionCreate,
    TaxCalculate,
    TaxElectionCreate,
    TaxRuleCreate,
)


class TaxEngineError(Exception):
    pass


class TaxEngineService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def jurisdiction(
        self,
        data: JurisdictionCreate,
    ) -> TaxJurisdiction:
        if data.parent_id is not None:
            parent_statement = select(TaxJurisdiction).where(
                TaxJurisdiction.id == data.parent_id,
                TaxJurisdiction.tenant_id == self.tenant_id,
                TaxJurisdiction.active.is_(True),
            )
            parent = await self.db.scalar(parent_statement)

            if parent is None:
                raise TaxEngineError("Parent jurisdiction was not found")

            if parent.country_code != data.country_code:
                raise TaxEngineError("Parent jurisdiction country differs")

        jurisdiction = TaxJurisdiction(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(jurisdiction)

        await self.db.commit()
        await self.db.refresh(jurisdiction)

        return jurisdiction

    async def rule(
        self,
        data: TaxRuleCreate,
    ) -> TaxRule:
        jurisdiction_statement = select(TaxJurisdiction).where(
            TaxJurisdiction.id == data.jurisdiction_id,
            TaxJurisdiction.tenant_id == self.tenant_id,
            TaxJurisdiction.active.is_(True),
        )
        jurisdiction = await self.db.scalar(jurisdiction_statement)

        if jurisdiction is None:
            raise TaxEngineError("Active jurisdiction was not found")

        if data.responsibility not in {
            "employee",
            "employer",
            "both",
        }:
            raise TaxEngineError("Invalid tax responsibility")

        rule = TaxRule(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(rule)

        await self.db.commit()
        await self.db.refresh(rule)

        return rule

    async def election(
        self,
        data: TaxElectionCreate,
    ) -> WorkerTaxElection:
        jurisdiction_statement = select(TaxJurisdiction).where(
            TaxJurisdiction.id == data.jurisdiction_id,
            TaxJurisdiction.tenant_id == self.tenant_id,
            TaxJurisdiction.active.is_(True),
        )
        jurisdiction = await self.db.scalar(jurisdiction_statement)

        if jurisdiction is None:
            raise TaxEngineError("Active jurisdiction was not found")

        election = WorkerTaxElection(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(election)

        await self.db.commit()
        await self.db.refresh(election)

        return election

    async def calculate(
        self,
        data: TaxCalculate,
    ) -> PayrollTaxCalculation:
        rule_statement = select(TaxRule).where(
            TaxRule.id == data.tax_rule_id,
            TaxRule.tenant_id == self.tenant_id,
            TaxRule.status == "active",
        )
        rule = await self.db.scalar(rule_statement)

        if rule is None:
            raise TaxEngineError("Active tax rule was not found")

        result = calculate_tax(
            taxable_wages=data.taxable_wages,
            rate=rule.rate,
            responsibility=rule.responsibility,
            wage_base=rule.annual_wage_base,
            additional_withholding=(data.additional_withholding),
            exempt=data.exempt,
        )

        calculation = PayrollTaxCalculation(
            tenant_id=self.tenant_id,
            payroll_worker_id=(data.payroll_worker_id),
            tax_rule_id=rule.id,
            taxable_wages=result.taxable_wages,
            employee_amount=result.employee_amount,
            employer_amount=result.employer_amount,
            explanation=result.explanation,
        )
        self.db.add(calculation)

        await self.db.commit()
        await self.db.refresh(calculation)

        return calculation

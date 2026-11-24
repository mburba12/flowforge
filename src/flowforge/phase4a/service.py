from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.platform.services import record_change

from .models import (
    BenefitEnrollment,
    BenefitPlan,
    CompensationRate,
    WorkerAssignment,
    WorkerBankAccount,
    WorkerProfile,
    WorkerTaxProfile,
    WorkLocation,
)
from .schemas import (
    AssignmentCreate,
    BankAccountCreate,
    BenefitEnrollmentCreate,
    BenefitPlanCreate,
    CompensationCreate,
    TaxProfileCreate,
    WorkerCreate,
    WorkLocationCreate,
)


class WorkforceError(Exception):
    pass


class WorkforceService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def create_worker(
        self,
        data: WorkerCreate,
    ) -> WorkerProfile:
        count_statement = (
            select(func.count())
            .select_from(WorkerProfile)
            .where(WorkerProfile.tenant_id == self.tenant_id)
        )
        count = await self.db.scalar(count_statement)

        worker = WorkerProfile(
            tenant_id=self.tenant_id,
            worker_number=(f"W-{int(count or 0) + 1:08d}"),
            **data.model_dump(),
        )
        self.db.add(worker)
        await self.db.flush()

        await record_change(
            self.db,
            self.tenant_id,
            self.user_id,
            "created",
            "worker",
            str(worker.id),
        )

        await self.db.commit()
        await self.db.refresh(worker)

        return worker

    async def create_location(
        self,
        data: WorkLocationCreate,
    ) -> WorkLocation:
        location = WorkLocation(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(location)

        await self.db.commit()
        await self.db.refresh(location)

        return location

    async def assign(
        self,
        worker_id: UUID,
        data: AssignmentCreate,
    ) -> WorkerAssignment:
        worker_statement = select(WorkerProfile).where(
            WorkerProfile.id == worker_id,
            WorkerProfile.tenant_id == self.tenant_id,
        )
        worker = await self.db.scalar(worker_statement)

        location_statement = select(WorkLocation).where(
            WorkLocation.id == data.work_location_id,
            WorkLocation.tenant_id == self.tenant_id,
        )
        location = await self.db.scalar(location_statement)

        if worker is None:
            raise WorkforceError("Worker was not found")

        if location is None:
            raise WorkforceError("Work location was not found")

        assignment = WorkerAssignment(
            tenant_id=self.tenant_id,
            worker_id=worker_id,
            **data.model_dump(),
        )
        self.db.add(assignment)

        await self.db.commit()
        await self.db.refresh(assignment)

        return assignment

    async def compensation(
        self,
        worker_id: UUID,
        data: CompensationCreate,
    ) -> CompensationRate:
        await self._require_worker(worker_id)

        overlap_statement = select(CompensationRate).where(
            CompensationRate.tenant_id == self.tenant_id,
            CompensationRate.worker_id == worker_id,
            CompensationRate.compensation_type == data.compensation_type,
            or_(
                CompensationRate.effective_to.is_(None),
                CompensationRate.effective_to >= data.effective_from,
            ),
        )

        if data.effective_to is not None:
            overlap_statement = overlap_statement.where(
                CompensationRate.effective_from <= data.effective_to
            )

        overlap = await self.db.scalar(overlap_statement)

        if overlap is not None:
            raise WorkforceError("Compensation period overlaps an existing rate")

        rate = CompensationRate(
            tenant_id=self.tenant_id,
            worker_id=worker_id,
            **data.model_dump(),
        )
        self.db.add(rate)

        await record_change(
            self.db,
            self.tenant_id,
            self.user_id,
            "created",
            "compensation_rate",
            str(rate.id),
        )

        await self.db.commit()
        await self.db.refresh(rate)

        return rate

    async def bank_account(
        self,
        worker_id: UUID,
        data: BankAccountCreate,
    ) -> WorkerBankAccount:
        await self._require_worker(worker_id)

        account = WorkerBankAccount(
            tenant_id=self.tenant_id,
            worker_id=worker_id,
            **data.model_dump(),
        )
        self.db.add(account)

        await record_change(
            self.db,
            self.tenant_id,
            self.user_id,
            "created",
            "worker_bank_account",
            str(account.id),
        )

        await self.db.commit()
        await self.db.refresh(account)

        return account

    async def tax_profile(
        self,
        worker_id: UUID,
        data: TaxProfileCreate,
    ) -> WorkerTaxProfile:
        await self._require_worker(worker_id)

        profile = WorkerTaxProfile(
            tenant_id=self.tenant_id,
            worker_id=worker_id,
            **data.model_dump(),
        )
        self.db.add(profile)

        await self.db.commit()
        await self.db.refresh(profile)

        return profile

    async def benefit_plan(
        self,
        data: BenefitPlanCreate,
    ) -> BenefitPlan:
        plan = BenefitPlan(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(plan)

        await self.db.commit()
        await self.db.refresh(plan)

        return plan

    async def enroll(
        self,
        worker_id: UUID,
        data: BenefitEnrollmentCreate,
    ) -> BenefitEnrollment:
        await self._require_worker(worker_id)

        plan_statement = select(BenefitPlan).where(
            BenefitPlan.id == data.plan_id,
            BenefitPlan.tenant_id == self.tenant_id,
            BenefitPlan.active.is_(True),
        )
        plan = await self.db.scalar(plan_statement)

        if plan is None:
            raise WorkforceError("Active benefit plan was not found")

        enrollment = BenefitEnrollment(
            tenant_id=self.tenant_id,
            worker_id=worker_id,
            **data.model_dump(),
        )
        self.db.add(enrollment)

        await self.db.commit()
        await self.db.refresh(enrollment)

        return enrollment

    async def _require_worker(
        self,
        worker_id: UUID,
    ) -> WorkerProfile:
        statement = select(WorkerProfile).where(
            WorkerProfile.id == worker_id,
            WorkerProfile.tenant_id == self.tenant_id,
        )
        worker = await self.db.scalar(statement)

        if worker is None:
            raise WorkforceError("Worker was not found")

        return worker

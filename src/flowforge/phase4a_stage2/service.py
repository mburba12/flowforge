from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase4a.models import WorkerProfile

from .models import (
    LeaveRequest,
    LeaveType,
    PayGroup,
    PayPeriod,
    TimeEntry,
    WorkSchedule,
)
from .schemas import (
    LeaveRequestCreate,
    LeaveTypeCreate,
    PayGroupCreate,
    PayPeriodCreate,
    ScheduleCreate,
    TimeEntryCreate,
)


class TimeLeaveError(Exception):
    pass


class TimeLeaveService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def schedule(
        self,
        data: ScheduleCreate,
    ) -> WorkSchedule:
        schedule = WorkSchedule(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(schedule)

        await self.db.commit()
        await self.db.refresh(schedule)

        return schedule

    async def time_entry(
        self,
        data: TimeEntryCreate,
    ) -> TimeEntry:
        worker_statement = select(WorkerProfile).where(
            WorkerProfile.id == data.worker_id,
            WorkerProfile.tenant_id == self.tenant_id,
        )
        worker = await self.db.scalar(worker_statement)

        if worker is None:
            raise TimeLeaveError("Worker was not found")

        entry = TimeEntry(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(entry)

        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    async def approve_time(
        self,
        entry_id: UUID,
    ) -> TimeEntry:
        entry_statement = select(TimeEntry).where(
            TimeEntry.id == entry_id,
            TimeEntry.tenant_id == self.tenant_id,
        )
        entry = await self.db.scalar(entry_statement)

        if entry is None:
            raise TimeLeaveError("Time entry was not found")

        if entry.status not in {
            "draft",
            "submitted",
        }:
            raise TimeLeaveError("Time entry cannot be approved")

        entry.status = "approved"
        entry.approved_by = self.user_id

        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    async def leave_type(
        self,
        data: LeaveTypeCreate,
    ) -> LeaveType:
        leave_type = LeaveType(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(leave_type)

        await self.db.commit()
        await self.db.refresh(leave_type)

        return leave_type

    async def leave_request(
        self,
        data: LeaveRequestCreate,
    ) -> LeaveRequest:
        worker_statement = select(WorkerProfile).where(
            WorkerProfile.id == data.worker_id,
            WorkerProfile.tenant_id == self.tenant_id,
        )
        worker = await self.db.scalar(worker_statement)

        if worker is None:
            raise TimeLeaveError("Worker was not found")

        leave_type_statement = select(LeaveType).where(
            LeaveType.id == data.leave_type_id,
            LeaveType.tenant_id == self.tenant_id,
            LeaveType.active.is_(True),
        )
        leave_type = await self.db.scalar(leave_type_statement)

        if leave_type is None:
            raise TimeLeaveError("Active leave type was not found")

        request = LeaveRequest(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(request)

        await self.db.commit()
        await self.db.refresh(request)

        return request

    async def pay_group(
        self,
        data: PayGroupCreate,
    ) -> PayGroup:
        group = PayGroup(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(group)

        await self.db.commit()
        await self.db.refresh(group)

        return group

    async def pay_period(
        self,
        data: PayPeriodCreate,
    ) -> PayPeriod:
        group_statement = select(PayGroup).where(
            PayGroup.id == data.pay_group_id,
            PayGroup.tenant_id == self.tenant_id,
            PayGroup.active.is_(True),
        )
        group = await self.db.scalar(group_statement)

        if group is None:
            raise TimeLeaveError("Active pay group was not found")

        period = PayPeriod(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(period)

        await self.db.commit()
        await self.db.refresh(period)

        return period

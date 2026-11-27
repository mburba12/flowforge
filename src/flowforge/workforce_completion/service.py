from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change

from .models import *


class CompletionService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def save(self, o, e):
        self.db.add(o)
        await self.db.flush()
        await record_change(self.db, self.ctx.tenant_id, self.ctx.user_id, "created", e, str(o.id))
        await self.db.commit()
        await self.db.refresh(o)
        return o

    async def get(self, m, id):
        x = await self.db.scalar(select(m).where(m.id == id, m.tenant_id == self.ctx.tenant_id))
        if not x:
            raise LookupError("Record not found")
        return x

    async def no_overlap(self, m, worker, start, end, exclude=None):
        cond = [
            m.tenant_id == self.ctx.tenant_id,
            m.worker_id == worker,
            or_(m.effective_to.is_(None), m.effective_to >= start),
            or_(end is None, m.effective_from <= end),
        ]
        if exclude:
            cond.append(m.id != exclude)
        if await self.db.scalar(select(m.id).where(*cond)):
            raise ValueError("Effective dates overlap")

    async def assignment(self, b):
        await self.no_overlap(Assignment, b.worker_id, b.effective_from, b.effective_to)
        return await self.save(
            Assignment(tenant_id=self.ctx.tenant_id, **b.model_dump()), "worker_assignment"
        )

    async def compensation(self, b):
        await self.no_overlap(Compensation, b.worker_id, b.effective_from, b.effective_to)
        return await self.save(
            Compensation(tenant_id=self.ctx.tenant_id, **b.model_dump()), "worker_compensation"
        )

    async def action(self, m, id, target, key, allowed):
        old = await self.db.scalar(
            select(WorkforceExecution).where(
                WorkforceExecution.tenant_id == self.ctx.tenant_id,
                WorkforceExecution.operation == target,
                WorkforceExecution.idempotency_key == key,
            )
        )
        if old:
            return old
        x = await self.get(m, id)
        if target not in allowed.get(x.status, set()):
            raise ValueError(f"Invalid transition {x.status}->{target}")
        if target == "approved" and hasattr(x, "approved_by"):
            x.approved_by = self.ctx.user_id
        if target == "completed" and hasattr(x, "completed_at"):
            x.completed_at = datetime.now(UTC)
        x.status = target
        e = WorkforceExecution(
            tenant_id=self.ctx.tenant_id,
            operation=target,
            idempotency_key=key,
            aggregate_type=m.__tablename__,
            aggregate_id=id,
            actor_user_id=self.ctx.user_id,
        )
        self.db.add(e)
        await self.db.commit()
        return x

    async def leave_balance(self, worker, policy):
        p = await self.get(LeavePolicy, policy)
        used = await self.db.scalar(
            select(func.coalesce(func.sum(LeaveRequest.units), 0)).where(
                LeaveRequest.tenant_id == self.ctx.tenant_id,
                LeaveRequest.worker_id == worker,
                LeaveRequest.policy_id == policy,
                LeaveRequest.status == "approved",
            )
        )
        return {
            "entitlement": p.annual_entitlement,
            "used": used,
            "available": p.annual_entitlement - used,
        }

    async def document_access(self, id):
        d = await self.get(WorkerDocument, id)
        return {
            "document_id": str(d.id),
            "storage_reference": d.storage_reference,
            "classification": d.classification,
            "legal_hold": d.legal_hold,
        }

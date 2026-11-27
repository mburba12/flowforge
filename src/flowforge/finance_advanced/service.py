from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change

from .models import *
from .schemas import *


class FinanceAdvancedService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def save(self, obj, entity):
        self.db.add(obj)
        await self.db.flush()
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "created", entity, str(obj.id)
        )
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def close_run(self, d: CloseRunCreate):
        return await self.save(
            CloseRun(tenant_id=self.ctx.tenant_id, created_by=self.ctx.user_id, **d.model_dump()),
            "finance_close_run",
        )

    async def recurring(self, d: RecurringJournalCreate):
        return await self.save(
            RecurringJournal(tenant_id=self.ctx.tenant_id, **d.model_dump()), "recurring_journal"
        )

    async def payment_batch(self, d: PaymentBatchCreate):
        return await self.save(
            PaymentBatch(tenant_id=self.ctx.tenant_id, **d.model_dump()), "payment_batch"
        )

    async def reconciliation(self, d: ReconciliationCreate):
        variance = d.source_balance - d.target_balance
        status = "reconciled" if abs(variance) <= d.tolerance else "open"
        return await self.save(
            ReconciliationSession(
                tenant_id=self.ctx.tenant_id, variance=variance, status=status, **d.model_dump()
            ),
            "reconciliation_session",
        )

    async def budget(self, d: BudgetVersionCreate):
        return await self.save(
            BudgetVersion(tenant_id=self.ctx.tenant_id, **d.model_dump()), "budget_version"
        )

    async def budget_line(self, version_id: UUID, d: BudgetLineCreate):
        v = await self.db.scalar(
            select(BudgetVersion).where(
                BudgetVersion.id == version_id, BudgetVersion.tenant_id == self.ctx.tenant_id
            )
        )
        if v is None:
            raise LookupError("Budget version not found")
        if v.locked:
            raise PermissionError("Budget version is locked")
        return await self.save(
            BudgetLine(tenant_id=self.ctx.tenant_id, version_id=version_id, **d.model_dump()),
            "budget_line",
        )

    async def consolidation(self, d: ConsolidationCreate):
        return await self.save(
            ConsolidationRun(
                tenant_id=self.ctx.tenant_id,
                created_by=self.ctx.user_id,
                status="balanced" if d.elimination_variance == 0 else "exception",
                **d.model_dump(),
            ),
            "consolidation_run",
        )

    async def asset(self, d: AssetCreate):
        if d.salvage_value > d.cost:
            raise ValueError("Salvage value exceeds cost")
        return await self.save(
            AssetRegister(tenant_id=self.ctx.tenant_id, **d.model_dump()), "asset"
        )

    async def depreciate(self, asset_id: UUID):
        a = await self.db.scalar(
            select(AssetRegister).where(
                AssetRegister.id == asset_id, AssetRegister.tenant_id == self.ctx.tenant_id
            )
        )
        if a is None:
            raise LookupError("Asset not found")
        amount = ((a.cost - a.salvage_value) / a.useful_life_periods).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        remaining = a.cost - a.salvage_value - a.accumulated_depreciation
        posted = min(amount, remaining)
        if posted <= 0:
            raise ValueError("Asset is fully depreciated")
        a.accumulated_depreciation += posted
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "depreciated", "asset", str(a.id)
        )
        await self.db.commit()
        return {
            "asset_id": str(a.id),
            "depreciation": posted,
            "accumulated": a.accumulated_depreciation,
        }

    async def list(self, model):
        return list(
            (
                await self.db.scalars(select(model).where(model.tenant_id == self.ctx.tenant_id))
            ).all()
        )

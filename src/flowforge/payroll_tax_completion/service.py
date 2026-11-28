from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase4a_stage3.models import PayrollRunWorker
from flowforge.platform.services import record_change

from .models import *  # noqa: F403, F405


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

    async def retro(self, b):
        return await self.save(
            RetroCalculation(
                tenant_id=self.ctx.tenant_id,
                difference=b.new_amount - b.old_amount,
                **b.model_dump(),
            ),
            "retro_calculation",
        )

    async def batch(self, b):
        total = Decimal(
            str(
                (
                    await self.db.scalar(
                        select(func.coalesce(func.sum(PayrollRunWorker.net_pay), 0)).where(
                            PayrollRunWorker.tenant_id == self.ctx.tenant_id,
                            PayrollRunWorker.payroll_run_id == b.payroll_run_id,
                        )
                    )
                )
                or 0
            )
        )
        return await self.save(
            PayrollPaymentBatch(tenant_id=self.ctx.tenant_id, total_amount=total, **b.model_dump()),
            "payroll_payment_batch",
        )

    async def batch_action(self, id, target, key):
        b = await self.get(PayrollPaymentBatch, id)
        allowed = {
            "draft": {"submitted", "voided"},
            "submitted": {"approved", "voided"},
            "approved": {"simulated_released", "voided"},
        }
        if target not in allowed.get(b.status, set()):
            raise ValueError("Invalid payment batch transition")
        if target == "approved":
            b.approved_by = self.ctx.user_id
        if target == "simulated_released":
            b.released_at = datetime.now(UTC)
            b.provider_reference = f"simulated-{b.id}"
        b.status = target
        await self.db.commit()
        return b

    async def filing(self, b):
        old = await self.db.scalar(
            select(TaxFilingSubmission).where(
                TaxFilingSubmission.tenant_id == self.ctx.tenant_id,
                TaxFilingSubmission.submission_key == b.submission_key,
            )
        )
        if old:
            return old
        return await self.save(
            TaxFilingSubmission(tenant_id=self.ctx.tenant_id, status="prepared", **b.model_dump()),
            "tax_filing_submission",
        )

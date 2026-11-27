from __future__ import annotations

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change

from .models import *


class BG08Service:
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

    async def subscription(self, b):
        p = await self.get(Plan, b.plan_id)
        renews = b.starts_on + timedelta(
            days={"monthly": 30, "quarterly": 90, "annual": 365}.get(p.billing_interval, 30)
        )
        status = "trialing" if p.trial_days else "active"
        return await self.save(
            Subscription(
                tenant_id=self.ctx.tenant_id, status=status, renews_on=renews, **b.model_dump()
            ),
            "subscription",
        )

    async def subscription_action(self, id, target, reason):
        x = await self.get(Subscription, id)
        allowed = {
            "trialing": {"active", "cancelled"},
            "active": {"paused", "cancelled", "renewed"},
            "paused": {"active", "cancelled"},
            "renewed": {"active", "cancelled"},
        }
        if target not in allowed.get(x.status, set()):
            raise ValueError("Invalid subscription transition")
        x.status = target
        x.cancel_reason = reason if target == "cancelled" else None
        if target == "renewed":
            x.renews_on = (x.renews_on or x.starts_on) + timedelta(days=30)
        await self.db.commit()
        return x

    async def usage(self, b):
        old = await self.db.scalar(
            select(UsageRecord).where(
                UsageRecord.tenant_id == self.ctx.tenant_id,
                UsageRecord.idempotency_key == b.idempotency_key,
            )
        )
        if old:
            return old
        return await self.save(
            UsageRecord(tenant_id=self.ctx.tenant_id, **b.model_dump()), "usage_record"
        )

    async def billing_run(self, b):
        if b.period_end < b.period_start:
            raise ValueError("Invalid billing period")
        subs = list(
            (
                await self.db.scalars(
                    select(Subscription).where(
                        Subscription.tenant_id == self.ctx.tenant_id,
                        Subscription.status.in_(["active", "trialing", "renewed"]),
                    )
                )
            ).all()
        )
        total = Decimal("0")
        for s in subs:
            p = await self.get(Plan, s.plan_id)
            usage = Decimal(
                str(
                    (
                        await self.db.scalar(
                            select(func.coalesce(func.sum(UsageRecord.quantity), 0)).where(
                                UsageRecord.tenant_id == self.ctx.tenant_id,
                                UsageRecord.subscription_id == s.id,
                                UsageRecord.occurred_at >= b.period_start,
                                UsageRecord.occurred_at <= b.period_end,
                            )
                        )
                    )
                    or 0
                )
            )
            total += p.price * (usage if p.billing_interval == "usage" else s.quantity)
        return await self.save(
            BillingRun(
                tenant_id=self.ctx.tenant_id,
                invoice_count=len(subs),
                total_amount=total,
                **b.model_dump(),
            ),
            "billing_run",
        )

    async def approve(self, m, id, target):
        x = await self.get(m, id)
        allowed = {
            "draft": {"submitted", "cancelled"},
            "submitted": {"approved", "rejected"},
            "approved": {"completed"},
        }
        if target not in allowed.get(x.status, set()):
            raise ValueError("Invalid transition")
        if target == "approved" and hasattr(x, "approved_by"):
            x.approved_by = self.ctx.user_id
        x.status = target
        await self.db.commit()
        return x

    async def project_profitability(self, id):
        p = await self.get(Project, id)
        time = Decimal(
            str(
                (
                    await self.db.scalar(
                        select(
                            func.coalesce(func.sum(ProjectTime.hours * ProjectTime.rate), 0)
                        ).where(
                            ProjectTime.tenant_id == self.ctx.tenant_id,
                            ProjectTime.project_id == id,
                            ProjectTime.status == "approved",
                        )
                    )
                )
                or 0
            )
        )
        expenses = Decimal(
            str(
                (
                    await self.db.scalar(
                        select(func.coalesce(func.sum(ProjectExpense.amount), 0)).where(
                            ProjectExpense.tenant_id == self.ctx.tenant_id,
                            ProjectExpense.project_id == id,
                            ProjectExpense.status == "approved",
                        )
                    )
                )
                or 0
            )
        )
        return {
            "project_id": str(id),
            "billable_value": time + expenses,
            "budget": p.budget,
            "variance": p.budget - (time + expenses),
        }

    async def depreciation(self, book_id):
        b = await self.get(AssetBook, book_id)
        base = b.salvage_value
        asset = await self.db.execute(
            select(
                __import__(
                    "flowforge.finance_advanced.models", fromlist=["AssetRegister"]
                ).AssetRegister
            ).where(
                __import__(
                    "flowforge.finance_advanced.models", fromlist=["AssetRegister"]
                ).AssetRegister.id
                == b.asset_id
            )
        )
        a = asset.scalar_one()
        amount = ((a.cost - b.salvage_value) / b.useful_life_periods).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )
        remaining = a.cost - b.salvage_value - b.accumulated_depreciation
        posted = min(amount, remaining)
        if posted <= 0:
            raise ValueError("Book fully depreciated")
        b.accumulated_depreciation += posted
        return await self.save(
            AssetTransaction(
                tenant_id=self.ctx.tenant_id,
                asset_id=a.id,
                book_id=b.id,
                transaction_type="depreciation",
                transaction_date=__import__("datetime").date.today(),
                amount=posted,
            ),
            "asset_transaction",
        )

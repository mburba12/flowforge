from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase2b.models import AccountingPeriod, JournalEntry, JournalLine
from flowforge.phase3a.models import APOpenItem, VendorInvoice
from flowforge.phase3b.models import AROpenItem, CustomerInvoice


class FinanceService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def _sum(self, model, column, *conditions) -> Decimal:
        return Decimal(
            str(
                (
                    await self.db.scalar(
                        select(func.coalesce(func.sum(column), 0))
                        .select_from(model)
                        .where(model.tenant_id == self.ctx.tenant_id, *conditions)
                    )
                )
                or 0
            )
        )

    async def dashboard(self, as_of: date) -> dict[str, object]:
        ap = await self._sum(APOpenItem, APOpenItem.open_amount, APOpenItem.status != "paid")
        ar = await self._sum(AROpenItem, AROpenItem.open_amount, AROpenItem.status != "paid")
        journals = int(
            (
                await self.db.scalar(
                    select(func.count())
                    .select_from(JournalEntry)
                    .where(
                        JournalEntry.tenant_id == self.ctx.tenant_id,
                        JournalEntry.status == "posted",
                    )
                )
            )
            or 0
        )
        open_periods = int(
            (
                await self.db.scalar(
                    select(func.count())
                    .select_from(AccountingPeriod)
                    .where(
                        AccountingPeriod.tenant_id == self.ctx.tenant_id,
                        AccountingPeriod.status == "open",
                    )
                )
            )
            or 0
        )
        return {
            "as_of": as_of,
            "ap_open": ap,
            "ar_open": ar,
            "net_working_capital": ar - ap,
            "posted_journals": journals,
            "open_periods": open_periods,
        }

    async def journal_integrity(self) -> dict[str, object]:
        rows = (
            await self.db.execute(
                select(
                    JournalLine.journal_id,
                    func.coalesce(func.sum(JournalLine.debit), 0),
                    func.coalesce(func.sum(JournalLine.credit), 0),
                )
                .where(JournalLine.tenant_id == self.ctx.tenant_id)
                .group_by(JournalLine.journal_id)
            )
        ).all()
        bad = [
            {"journal_id": str(i), "debit": str(d), "credit": str(c)} for i, d, c in rows if d != c
        ]
        return {
            "journals_checked": len(rows),
            "unbalanced_count": len(bad),
            "unbalanced": bad,
            "balanced": not bad,
        }

    async def subledger_integrity(self) -> dict[str, object]:
        ap_inv = await self._sum(
            VendorInvoice, VendorInvoice.total_amount, VendorInvoice.status.in_(["posted", "paid"])
        )
        ap_open = await self._sum(APOpenItem, APOpenItem.open_amount, APOpenItem.status != "paid")
        ar_inv = await self._sum(
            CustomerInvoice,
            CustomerInvoice.total_amount,
            CustomerInvoice.status.in_(["posted", "partially_paid", "paid"]),
        )
        ar_open = await self._sum(AROpenItem, AROpenItem.open_amount, AROpenItem.status != "paid")
        return {
            "ap": {"posted_invoices": ap_inv, "open_items": ap_open},
            "ar": {"posted_invoices": ar_inv, "open_items": ar_open},
        }

    async def period_readiness(self) -> dict[str, object]:
        periods = list(
            (
                await self.db.scalars(
                    select(AccountingPeriod)
                    .where(AccountingPeriod.tenant_id == self.ctx.tenant_id)
                    .order_by(AccountingPeriod.start_date)
                )
            ).all()
        )
        return {
            "count": len(periods),
            "periods": [
                {
                    "id": str(x.id),
                    "code": x.period_code,
                    "status": x.status,
                    "start": x.start_date,
                    "end": x.end_date,
                }
                for x in periods
            ],
        }

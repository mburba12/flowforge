from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.finance_advanced.models import AssetRegister, PaymentBatch, RecurringJournal
from flowforge.finance_completion.models import (
    AccrualDefinition,
    FinanceExecution,
    PaymentBatchItem,
    ReconciliationItem,
)
from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase2b.models import Account, AccountBalance, JournalEntry, JournalLine
from flowforge.platform.services import record_change


class FinalFinanceService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def _existing(self, t, key):
        return await self.db.scalar(
            select(FinanceExecution).where(
                FinanceExecution.tenant_id == self.ctx.tenant_id,
                FinanceExecution.execution_type == t,
                FinanceExecution.idempotency_key == key,
            )
        )

    async def journal(
        self,
        *,
        kind: str,
        key: str,
        ledger_id: UUID,
        period_id: UUID,
        journal_date: date,
        description: str,
        lines: list[tuple[UUID, Decimal, Decimal]],
    ):
        old = await self._existing(kind, key)
        if old:
            return {"idempotent": True, "execution_id": str(old.id), "result": old.result_json}
        debit = sum((x[1] for x in lines), Decimal("0"))
        credit = sum((x[2] for x in lines), Decimal("0"))
        if debit <= 0 or debit != credit:
            raise ValueError("Generated journal is not balanced")
        j = JournalEntry(
            tenant_id=self.ctx.tenant_id,
            ledger_id=ledger_id,
            period_id=period_id,
            journal_date=journal_date,
            description=description,
            status="draft",
            created_by=self.ctx.user_id,
        )
        self.db.add(j)
        await self.db.flush()
        for account_id, d, c in lines:
            self.db.add(
                JournalLine(
                    tenant_id=self.ctx.tenant_id,
                    journal_id=j.id,
                    account_id=account_id,
                    debit=d,
                    credit=c,
                    currency_code="USD",
                )
            )
        e = FinanceExecution(
            tenant_id=self.ctx.tenant_id,
            execution_type=kind,
            source_id=j.id,
            idempotency_key=key,
            status="completed",
            result_json=f'{{"journal_id":"{j.id}"}}',
            actor_user_id=self.ctx.user_id,
        )
        self.db.add(e)
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "generated", "journal", str(j.id)
        )
        await self.db.commit()
        return {"idempotent": False, "journal_id": str(j.id), "execution_id": str(e.id)}

    async def recurring(self, rid: UUID, key: str, period_id: UUID, journal_date: date):
        r = await self.db.scalar(
            select(RecurringJournal).where(
                RecurringJournal.id == rid,
                RecurringJournal.tenant_id == self.ctx.tenant_id,
                RecurringJournal.active.is_(True),
            )
        )
        if not r:
            raise LookupError("Recurring journal not found")
        out = await self.journal(
            kind="recurring_post",
            key=key,
            ledger_id=r.ledger_id,
            period_id=period_id,
            journal_date=journal_date,
            description=r.description,
            lines=[
                (r.debit_account_id, r.amount, Decimal("0")),
                (r.credit_account_id, Decimal("0"), r.amount),
            ],
        )
        r.next_run_date = r.next_run_date + timedelta(
            days={"daily": 1, "weekly": 7, "monthly": 30, "quarterly": 90, "annual": 365}.get(
                r.frequency, 30
            )
        )
        await self.db.commit()
        return out

    async def accrual(self, aid: UUID, key: str, period_id: UUID, journal_date: date):
        a = await self.db.scalar(
            select(AccrualDefinition).where(
                AccrualDefinition.id == aid, AccrualDefinition.tenant_id == self.ctx.tenant_id
            )
        )
        if not a:
            raise LookupError("Accrual not found")
        posted = await self.journal(
            kind="accrual_post",
            key=key,
            ledger_id=a.ledger_id,
            period_id=period_id,
            journal_date=journal_date,
            description=f"Accrual {a.code}",
            lines=[
                (a.debit_account_id, a.amount, Decimal("0")),
                (a.credit_account_id, Decimal("0"), a.amount),
            ],
        )
        posted["reversal_required"] = True
        posted["reversal_date"] = str(journal_date + timedelta(days=1))
        return posted

    async def allocation(self, b):
        if sum(x.basis_points for x in b.targets) != 10000:
            raise ValueError("Allocation basis points must total 10000")
        lines = [(b.source_account_id, Decimal("0"), b.amount)]
        allocated = Decimal("0")
        for i, t in enumerate(b.targets):
            amount = (
                b.amount - allocated
                if i == len(b.targets) - 1
                else (b.amount * Decimal(t.basis_points) / Decimal(10000)).quantize(Decimal(".01"))
            )
            allocated += amount
            lines.append((t.account_id, amount, Decimal("0")))
        return await self.journal(
            kind="allocation_post",
            key=b.idempotency_key,
            ledger_id=await self._ledger(b.source_account_id),
            period_id=b.period_id,
            journal_date=b.journal_date,
            description="Allocation run",
            lines=lines,
        )

    async def _ledger(self, account_id):
        a = await self.db.scalar(
            select(Account).where(Account.id == account_id, Account.tenant_id == self.ctx.tenant_id)
        )
        if not a:
            raise LookupError("Account not found")
        return a.ledger_id

    async def payment(self, bid, b, reverse=False):
        batch = await self.db.scalar(
            select(PaymentBatch).where(
                PaymentBatch.id == bid, PaymentBatch.tenant_id == self.ctx.tenant_id
            )
        )
        if not batch:
            raise LookupError("Batch not found")
        amount = batch.total_amount
        kind = "payment_reverse" if reverse else "payment_apply"
        lines = [
            (
                b.cash_account_id,
                amount if reverse else Decimal("0"),
                Decimal("0") if reverse else amount,
            ),
            (
                b.offset_account_id,
                Decimal("0") if reverse else amount,
                amount if reverse else Decimal("0"),
            ),
        ]
        out = await self.journal(
            kind=kind,
            key=b.idempotency_key,
            ledger_id=await self._ledger(b.cash_account_id),
            period_id=b.period_id,
            journal_date=b.journal_date,
            description=f"{kind} {batch.batch_number}",
            lines=lines,
        )
        batch.status = "reversed" if reverse else "applied"
        await self.db.execute(
            PaymentBatchItem.__table__.update()  # type: ignore[attr-defined]
            .where(
                PaymentBatchItem.batch_id == bid, PaymentBatchItem.tenant_id == self.ctx.tenant_id
            )
            .values(status=batch.status)
        )
        await self.db.commit()
        return out

    async def match(self, sid, item_ids, target, unmatch=False):
        items = list(
            (
                await self.db.scalars(
                    select(ReconciliationItem).where(
                        ReconciliationItem.session_id == sid,
                        ReconciliationItem.tenant_id == self.ctx.tenant_id,
                        ReconciliationItem.id.in_(item_ids),
                    )
                )
            ).all()
        )
        if len(items) != len(item_ids):
            raise LookupError("Reconciliation item not found")
        group = None if unmatch else uuid4()
        for x in items:
            x.status = "unmatched" if unmatch else "matched"
            x.match_group = group
            x.target_reference = None if unmatch else target
        await self.db.commit()
        return {
            "items": len(items),
            "status": "unmatched" if unmatch else "matched",
            "match_group": str(group) if group else None,
        }

    async def asset_post(self, asset_id, b):
        a = await self.db.scalar(
            select(AssetRegister).where(
                AssetRegister.id == asset_id, AssetRegister.tenant_id == self.ctx.tenant_id
            )
        )
        if not a:
            raise LookupError("Asset not found")
        out = await self.journal(
            kind=f"asset_{b.posting_type}",
            key=b.idempotency_key,
            ledger_id=b.ledger_id,
            period_id=b.period_id,
            journal_date=b.journal_date,
            description=f"Asset {a.asset_number} {b.posting_type}",
            lines=[
                (b.debit_account_id, b.amount, Decimal("0")),
                (b.credit_account_id, Decimal("0"), b.amount),
            ],
        )
        if b.posting_type == "disposal":
            a.status = "disposed"
        await self.db.commit()
        return out

    async def reports(self, b):
        async def balances(pid):
            rows = (
                await self.db.execute(
                    select(
                        Account.account_type,
                        Account.id,
                        Account.account_code,
                        Account.name,
                        AccountBalance.debit_total,
                        AccountBalance.credit_total,
                    )
                    .join(AccountBalance, AccountBalance.account_id == Account.id)
                    .where(
                        Account.tenant_id == self.ctx.tenant_id,
                        AccountBalance.tenant_id == self.ctx.tenant_id,
                        AccountBalance.ledger_id == b.ledger_id,
                        AccountBalance.period_id == pid,
                    )
                )
            ).all()
            return [
                {
                    "type": t,
                    "account_id": str(i),
                    "code": c,
                    "name": n,
                    "balance": Decimal(str(d)) - Decimal(str(cr)),
                }
                for t, i, c, n, d, cr in rows
            ]

        current = await balances(b.period_id)
        comparison = await balances(b.comparison_period_id) if b.comparison_period_id else []
        cash_flow = sum(
            (x["balance"] for x in current if x["type"] in ("asset", "liability")), Decimal("0")
        )
        return {
            "current": current,
            "comparison": comparison,
            "cash_flow_proxy": cash_flow,
            "drill_through_supported": True,
        }

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.errors import RuleViolation
from flowforge.finance_advanced.models import (
    CloseRun,
    PaymentBatch,
    ReconciliationSession,
    RecurringJournal,
)
from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase2b.models import Account, AccountBalance, AccountingPeriod
from flowforge.platform.approval import blocks_self_approval
from flowforge.platform.services import record_change

from .models import (
    FinanceExecution,
    PaymentBatchItem,
    ReconciliationItem,
)


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

    async def execution(self, t: str, sid: UUID, key: str, result: dict[str, Any]):
        old = await self.db.scalar(
            select(FinanceExecution).where(
                FinanceExecution.tenant_id == self.ctx.tenant_id,
                FinanceExecution.execution_type == t,
                FinanceExecution.idempotency_key == key,
            )
        )
        if old:
            return old
        return await self.save(
            FinanceExecution(
                tenant_id=self.ctx.tenant_id,
                execution_type=t,
                source_id=sid,
                idempotency_key=key,
                status="completed",
                result_json=json.dumps(result, default=str),
                actor_user_id=self.ctx.user_id,
            ),
            "finance_execution",
        )

    async def execute_recurring(self, rid: UUID, key: str):
        r = await self.db.scalar(
            select(RecurringJournal).where(
                RecurringJournal.id == rid,
                RecurringJournal.tenant_id == self.ctx.tenant_id,
                RecurringJournal.active.is_(True),
            )
        )
        if not r:
            raise LookupError("Active recurring journal not found")
        return await self.execution(
            "recurring_journal",
            rid,
            key,
            {
                "amount": r.amount,
                "debit_account_id": r.debit_account_id,
                "credit_account_id": r.credit_account_id,
                "posting_required": True,
            },
        )

    async def close_period(self, cid: UUID, key: str):
        c = await self.db.scalar(
            select(CloseRun).where(CloseRun.id == cid, CloseRun.tenant_id == self.ctx.tenant_id)
        )
        if not c:
            raise LookupError("Close run not found")
        if blocks_self_approval(c.created_by, self.ctx.user_id):
            raise RuleViolation("Creator cannot approve close run")
        period = await self.db.scalar(
            select(AccountingPeriod).where(
                AccountingPeriod.id == c.period_id, AccountingPeriod.tenant_id == self.ctx.tenant_id
            )
        )
        if not period:
            raise LookupError("Period not found")
        period.status = "closed"
        c.status = "closed"
        c.approved_by = self.ctx.user_id
        await self.db.commit()
        return await self.execution(
            "period_close", cid, key, {"period_id": period.id, "status": "closed"}
        )

    async def reopen_period(self, cid: UUID, key: str):
        c = await self.db.scalar(
            select(CloseRun).where(CloseRun.id == cid, CloseRun.tenant_id == self.ctx.tenant_id)
        )
        if not c:
            raise LookupError("Close run not found")
        period = await self.db.scalar(
            select(AccountingPeriod).where(
                AccountingPeriod.id == c.period_id, AccountingPeriod.tenant_id == self.ctx.tenant_id
            )
        )
        if period is None:
            raise LookupError("Accounting period not found")
        period.status = "open"
        c.status = "reopened"
        await self.db.commit()
        return await self.execution("period_reopen", cid, key, {"status": "open"})

    async def approve_batch(self, bid: UUID, key: str):
        """Approve a draft payment batch whose items add up to its total."""
        b = await self.db.scalar(
            select(PaymentBatch).where(
                PaymentBatch.id == bid, PaymentBatch.tenant_id == self.ctx.tenant_id
            )
        )
        if not b:
            raise LookupError("Payment batch not found")
        if b.approved_by is not None:
            raise ValueError("Payment batch is already approved")
        items = list(
            (
                await self.db.scalars(
                    select(PaymentBatchItem).where(
                        PaymentBatchItem.batch_id == bid,
                        PaymentBatchItem.tenant_id == self.ctx.tenant_id,
                    )
                )
            ).all()
        )
        total = sum((x.amount for x in items), Decimal("0"))
        if not items or total != b.total_amount:
            raise ValueError("Payment batch items do not match header total")
        b.approved_by = self.ctx.user_id
        b.status = "approved"
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "approved", "payment_batch", str(bid)
        )
        await self.db.commit()
        return await self.execution(
            "payment_approve", bid, key, {"items": len(items), "total": total}
        )

    async def release_batch(self, bid: UUID, key: str):
        b = await self.db.scalar(
            select(PaymentBatch).where(
                PaymentBatch.id == bid, PaymentBatch.tenant_id == self.ctx.tenant_id
            )
        )
        if not b:
            raise LookupError("Payment batch not found")
        items = list(
            (
                await self.db.scalars(
                    select(PaymentBatchItem).where(
                        PaymentBatchItem.batch_id == bid,
                        PaymentBatchItem.tenant_id == self.ctx.tenant_id,
                    )
                )
            ).all()
        )
        total = sum((x.amount for x in items), Decimal("0"))
        if not items or total != b.total_amount:
            raise ValueError("Payment batch items do not match header total")
        if b.approved_by is None:
            raise RuleViolation("Payment batch requires approval")
        for x in items:
            x.status = "simulated_paid"
            x.provider_reference = f"simulated-{x.id}"
        b.status = "simulated_released"
        await self.db.commit()
        return await self.execution(
            "payment_release",
            bid,
            key,
            {"items": len(items), "total": total, "provider": "simulated"},
        )

    async def certify_reconciliation(self, sid: UUID, key: str):
        s = await self.db.scalar(
            select(ReconciliationSession).where(
                ReconciliationSession.id == sid,
                ReconciliationSession.tenant_id == self.ctx.tenant_id,
            )
        )
        if not s:
            raise LookupError("Reconciliation not found")
        unmatched = int(
            (
                await self.db.scalar(
                    select(func.count())
                    .select_from(ReconciliationItem)
                    .where(
                        ReconciliationItem.session_id == sid,
                        ReconciliationItem.tenant_id == self.ctx.tenant_id,
                        ReconciliationItem.status != "matched",
                    )
                )
            )
            or 0
        )
        if unmatched or abs(s.variance) > s.tolerance:
            raise ValueError("Reconciliation contains unresolved items or variance")
        s.status = "certified"
        s.certified_by = self.ctx.user_id
        await self.db.commit()
        return await self.execution(
            "reconciliation_certification", sid, key, {"status": "certified"}
        )

    async def statement(self, ledger_id: UUID, period_id: UUID):
        rows = (
            await self.db.execute(
                select(
                    Account.account_type,
                    func.coalesce(
                        func.sum(AccountBalance.debit_total - AccountBalance.credit_total), 0
                    ),
                )
                .join(AccountBalance, AccountBalance.account_id == Account.id)
                .where(
                    Account.tenant_id == self.ctx.tenant_id,
                    AccountBalance.tenant_id == self.ctx.tenant_id,
                    AccountBalance.ledger_id == ledger_id,
                    AccountBalance.period_id == period_id,
                )
                .group_by(Account.account_type)
            )
        ).all()
        vals = {str(t): Decimal(str(v)) for t, v in rows}
        assets = vals.get("asset", Decimal("0"))
        liabilities = -vals.get("liability", Decimal("0"))
        equity = -vals.get("equity", Decimal("0"))
        revenue = -vals.get("revenue", Decimal("0"))
        expense = vals.get("expense", Decimal("0"))
        return {
            "income_statement": {
                "revenue": revenue,
                "expense": expense,
                "net_income": revenue - expense,
            },
            "balance_sheet": {
                "assets": assets,
                "liabilities": liabilities,
                "equity": equity,
                "balanced": assets == liabilities + equity,
            },
            "account_type_balances": vals,
        }

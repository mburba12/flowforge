from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase2b.models import JournalEntry, JournalLine
from flowforge.phase2b.posting import PostingError, PostingLine, post_system_journal

from .integration_models import (
    APReconciliationRun,
    VendorPayment,
    VendorPaymentAllocation,
)
from .models import APOpenItem


class APPaymentError(Exception):
    pass


class APPaymentService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def pay_open_item(
        self,
        open_item_id: UUID,
        amount: Decimal,
        payment_date: date,
        ledger_id: UUID,
        period_id: UUID,
        ap_account_id: UUID,
        cash_account_id: UUID,
        currency_code: str,
    ) -> VendorPayment:
        item = await self.db.scalar(
            select(APOpenItem).where(
                APOpenItem.id == open_item_id,
                APOpenItem.tenant_id == self.tenant_id,
            )
        )
        if item is None or item.status != "open":
            raise APPaymentError("Open item is unavailable")
        if amount <= 0 or amount > item.open_amount:
            raise APPaymentError("Invalid payment amount")

        payment = VendorPayment(
            tenant_id=self.tenant_id,
            vendor_id=item.vendor_id,
            payment_date=payment_date,
            amount=amount,
        )
        self.db.add(payment)
        await self.db.flush()
        self.db.add(
            VendorPaymentAllocation(
                tenant_id=self.tenant_id,
                payment_id=payment.id,
                open_item_id=item.id,
                amount=amount,
            )
        )

        try:
            journal = await post_system_journal(
                self.db,
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                ledger_id=ledger_id,
                period_id=period_id,
                journal_number=f"APPAY-{str(payment.id)[:8]}",
                journal_date=payment_date,
                description="Vendor payment",
                currency_code=currency_code,
                lines=[
                    PostingLine(ap_account_id, amount, Decimal("0"), "Clear accounts payable"),
                    PostingLine(cash_account_id, Decimal("0"), amount, "Vendor payment cash"),
                ],
            )
        except PostingError as exc:
            raise APPaymentError(str(exc)) from exc
        payment.journal_id = journal.id
        item.open_amount -= amount
        if item.open_amount == 0:
            item.status = "paid"
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def reconcile(
        self,
        ledger_id: UUID,
        period_id: UUID,
        ap_account_id: UUID,
    ) -> APReconciliationRun:
        open_items = list(
            (
                await self.db.scalars(
                    select(APOpenItem).where(
                        APOpenItem.tenant_id == self.tenant_id,
                    )
                )
            ).all()
        )
        subledger_total = sum(
            (item.open_amount for item in open_items),
            Decimal("0"),
        )
        lines = list(
            (
                await self.db.scalars(
                    select(JournalLine)
                    .join(JournalEntry, JournalEntry.id == JournalLine.journal_id)
                    .where(
                        JournalEntry.tenant_id == self.tenant_id,
                        JournalEntry.ledger_id == ledger_id,
                        JournalEntry.period_id == period_id,
                        JournalLine.account_id == ap_account_id,
                    )
                )
            ).all()
        )
        gl_total = sum(
            (line.credit - line.debit for line in lines),
            Decimal("0"),
        )
        status = "reconciled" if subledger_total == gl_total else "exception"
        run = APReconciliationRun(
            tenant_id=self.tenant_id,
            ledger_id=ledger_id,
            period_id=period_id,
            subledger_total=subledger_total,
            gl_total=gl_total,
            status=status,
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Account, AccountBalance, AccountingPeriod, JournalEntry, JournalLine


class PostingError(Exception):
    pass


class PostingEngine:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def post(self, journal_id: UUID) -> JournalEntry:
        journal = await self.db.scalar(
            select(JournalEntry).where(
                JournalEntry.id == journal_id,
                JournalEntry.tenant_id == self.tenant_id,
            )
        )
        if journal is None:
            raise PostingError("Journal not found")
        if journal.status != "approved":
            raise PostingError("Only approved journals can post")
        period = await self.db.scalar(
            select(AccountingPeriod).where(
                AccountingPeriod.id == journal.period_id,
                AccountingPeriod.tenant_id == self.tenant_id,
            )
        )
        if period is None or period.status != "open":
            raise PostingError("Accounting period is not open")
        lines = list(
            (
                await self.db.scalars(
                    select(JournalLine).where(JournalLine.journal_id == journal.id)
                )
            ).all()
        )
        debit = sum((line.debit for line in lines), Decimal("0"))
        credit = sum((line.credit for line in lines), Decimal("0"))
        if debit != credit:
            raise PostingError("Journal is unbalanced")
        for line in lines:
            account = await self.db.scalar(
                select(Account).where(
                    Account.id == line.account_id,
                    Account.tenant_id == self.tenant_id,
                    Account.active.is_(True),
                    Account.posting_allowed.is_(True),
                )
            )
            if account is None:
                raise PostingError("Account is not postable")
            balance = await self.db.scalar(
                select(AccountBalance).where(
                    AccountBalance.tenant_id == self.tenant_id,
                    AccountBalance.ledger_id == journal.ledger_id,
                    AccountBalance.period_id == journal.period_id,
                    AccountBalance.account_id == line.account_id,
                )
            )
            if balance is None:
                balance = AccountBalance(
                    tenant_id=self.tenant_id,
                    ledger_id=journal.ledger_id,
                    period_id=journal.period_id,
                    account_id=line.account_id,
                    debit_total=Decimal("0"),
                    credit_total=Decimal("0"),
                )
                self.db.add(balance)
            balance.debit_total += line.debit
            balance.credit_total += line.credit
        journal.status = "posted"
        journal.posted_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(journal)
        return journal

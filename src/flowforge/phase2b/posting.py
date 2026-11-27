from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Account, AccountBalance, AccountingPeriod, JournalEntry, JournalLine


class PostingError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class PostingLine:
    account_id: UUID
    debit: Decimal
    credit: Decimal
    description: str | None = None


async def _open_period(
    db: AsyncSession, tenant_id: UUID, period_id: UUID, journal_date: date | None
) -> AccountingPeriod:
    period = await db.scalar(
        select(AccountingPeriod).where(
            AccountingPeriod.id == period_id,
            AccountingPeriod.tenant_id == tenant_id,
        )
    )
    if period is None or period.status != "open":
        raise PostingError("Accounting period is not open")
    if journal_date is not None and not (period.start_date <= journal_date <= period.end_date):
        raise PostingError("Journal date is outside the accounting period")
    return period


async def _postable_account(
    db: AsyncSession, tenant_id: UUID, ledger_id: UUID, account_id: UUID
) -> Account:
    account = await db.scalar(
        select(Account).where(
            Account.id == account_id,
            Account.tenant_id == tenant_id,
            Account.ledger_id == ledger_id,
            Account.active.is_(True),
            Account.posting_allowed.is_(True),
        )
    )
    if account is None:
        raise PostingError("Account is not postable")
    return account


async def _apply_to_balances(
    db: AsyncSession,
    tenant_id: UUID,
    ledger_id: UUID,
    period_id: UUID,
    lines: Sequence[JournalLine],
) -> None:
    for line in lines:
        balance = await db.scalar(
            select(AccountBalance)
            .where(
                AccountBalance.tenant_id == tenant_id,
                AccountBalance.ledger_id == ledger_id,
                AccountBalance.period_id == period_id,
                AccountBalance.account_id == line.account_id,
            )
            .with_for_update()
        )
        if balance is None:
            balance = AccountBalance(
                tenant_id=tenant_id,
                ledger_id=ledger_id,
                period_id=period_id,
                account_id=line.account_id,
                debit_total=Decimal("0"),
                credit_total=Decimal("0"),
            )
            db.add(balance)
            await db.flush()
        balance.debit_total += line.debit
        balance.credit_total += line.credit


async def post_system_journal(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    ledger_id: UUID,
    period_id: UUID,
    journal_number: str,
    journal_date: date,
    description: str,
    currency_code: str,
    lines: Sequence[PostingLine],
) -> JournalEntry:
    """Validate and post a subledger-generated journal in the caller's transaction.

    Subledgers (AP, AR, inventory, payroll, tax) generate journals from business
    documents that were already approved in their own workflow. They must still
    obey the same ledger rules as manual journals: open period, journal date in
    the period, postable accounts in the ledger, balanced and non-zero, and the
    posted amounts must reach account balances (and so the trial balance).

    Does not commit; the caller commits the business document and the journal
    together, so a PostingError leaves neither behind.
    """
    await _open_period(db, tenant_id, period_id, journal_date)
    effective = [line for line in lines if line.debit != 0 or line.credit != 0]
    if not effective:
        raise PostingError("Journal has no amounts")
    for line in effective:
        if line.debit < 0 or line.credit < 0 or (line.debit > 0 and line.credit > 0):
            raise PostingError("Each journal line must have exactly one positive side")
        await _postable_account(db, tenant_id, ledger_id, line.account_id)
    debit = sum((line.debit for line in effective), Decimal("0"))
    credit = sum((line.credit for line in effective), Decimal("0"))
    if debit != credit:
        raise PostingError("Journal is unbalanced")

    journal = JournalEntry(
        tenant_id=tenant_id,
        ledger_id=ledger_id,
        period_id=period_id,
        journal_number=journal_number,
        journal_date=journal_date,
        description=description,
        status="posted",
        created_by=user_id,
        approved_by=user_id,
        posted_at=datetime.now(UTC),
    )
    db.add(journal)
    await db.flush()
    journal_lines = [
        JournalLine(
            tenant_id=tenant_id,
            journal_id=journal.id,
            line_number=number,
            account_id=line.account_id,
            description=line.description,
            debit=line.debit,
            credit=line.credit,
            currency_code=currency_code,
        )
        for number, line in enumerate(effective, start=1)
    ]
    db.add_all(journal_lines)
    await db.flush()
    await _apply_to_balances(db, tenant_id, ledger_id, period_id, journal_lines)
    return journal


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
        await _open_period(self.db, self.tenant_id, journal.period_id, journal.journal_date)
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
            await _postable_account(self.db, self.tenant_id, journal.ledger_id, line.account_id)
        await _apply_to_balances(
            self.db, self.tenant_id, journal.ledger_id, journal.period_id, lines
        )
        journal.status = "posted"
        journal.posted_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(journal)
        return journal

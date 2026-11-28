from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.platform.numbering import next_number
from flowforge.platform.services import record_change

from .models import (
    Account,
    AccountingPeriod,
    Currency,
    FiscalCalendar,
    JournalEntry,
    JournalLine,
    Ledger,
)
from .schemas import (
    AccountCreate,
    CalendarCreate,
    CurrencyCreate,
    JournalCreate,
    LedgerCreate,
    PeriodCreate,
)


class LedgerService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def currency(self, data: CurrencyCreate) -> Currency:
        code = data.code.upper()
        item = await self.db.get(Currency, code)
        if item is None:
            item = Currency(code=code, name=data.name, decimal_places=data.decimal_places)
            self.db.add(item)
            await self.db.commit()
        return item

    async def calendar(self, data: CalendarCreate) -> FiscalCalendar:
        item = FiscalCalendar(tenant_id=self.tenant_id, **data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def period(self, data: PeriodCreate) -> AccountingPeriod:
        item = AccountingPeriod(tenant_id=self.tenant_id, status="open", **data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def ledger(self, data: LedgerCreate) -> Ledger:
        item = Ledger(tenant_id=self.tenant_id, **data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def account(self, data: AccountCreate) -> Account:
        item = Account(tenant_id=self.tenant_id, **data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def journal(self, data: JournalCreate) -> JournalEntry:
        # Refuse accounts of another ledger (or closed to posting) now, not at posting time.
        from .posting import _postable_account

        for line in data.lines:
            await _postable_account(self.db, self.tenant_id, data.ledger_id, line.account_id)
        item = JournalEntry(
            tenant_id=self.tenant_id,
            ledger_id=data.ledger_id,
            period_id=data.period_id,
            journal_number=await next_number(self.db, self.tenant_id, "journal"),
            journal_date=data.journal_date,
            description=data.description,
            created_by=self.user_id,
        )
        self.db.add(item)
        await self.db.flush()
        for index, line in enumerate(data.lines, start=1):
            self.db.add(
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=item.id,
                    line_number=index,
                    **line.model_dump(),
                )
            )
        await record_change(
            self.db, self.tenant_id, self.user_id, "created", "journal", str(item.id)
        )
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def trial_balance(self, ledger_id: UUID, period_id: UUID) -> dict[str, Decimal]:
        from .models import AccountBalance

        balances = list(
            (
                await self.db.scalars(
                    select(AccountBalance).where(
                        AccountBalance.tenant_id == self.tenant_id,
                        AccountBalance.ledger_id == ledger_id,
                        AccountBalance.period_id == period_id,
                    )
                )
            ).all()
        )
        return {
            "debit": sum((b.debit_total for b in balances), Decimal("0")),
            "credit": sum((b.credit_total for b in balances), Decimal("0")),
        }

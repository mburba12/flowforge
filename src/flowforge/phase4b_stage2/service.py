from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase2b.models import (
    JournalEntry,
    JournalLine,
)

from .models import (
    TaxLiability,
    TaxNotice,
    TaxReconciliationRun,
    TaxRemittance,
    TaxRemittanceAllocation,
    TaxReturn,
    TaxReturnLine,
)
from .schemas import (
    TaxLiabilityCreate,
    TaxNoticeCreate,
    TaxRemittanceCreate,
    TaxReturnCreate,
)


class TaxFilingError(Exception):
    pass


class TaxFilingService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def liability(
        self,
        data: TaxLiabilityCreate,
    ) -> TaxLiability:
        liability = TaxLiability(
            tenant_id=self.tenant_id,
            open_amount=data.amount,
            **data.model_dump(),
        )
        self.db.add(liability)

        await self.db.commit()
        await self.db.refresh(liability)

        return liability

    async def tax_return(
        self,
        data: TaxReturnCreate,
    ) -> TaxReturn:
        return_data = data.model_dump(
            exclude={
                "taxable_wages",
                "tax_amount",
                "tax_code",
            }
        )

        tax_return = TaxReturn(
            tenant_id=self.tenant_id,
            total_tax=data.tax_amount,
            created_by=self.user_id,
            **return_data,
        )
        self.db.add(tax_return)
        await self.db.flush()

        self.db.add(
            TaxReturnLine(
                tenant_id=self.tenant_id,
                tax_return_id=tax_return.id,
                tax_code=data.tax_code,
                taxable_wages=data.taxable_wages,
                tax_amount=data.tax_amount,
            )
        )

        await self.db.commit()
        await self.db.refresh(tax_return)

        return tax_return

    async def approve_return(
        self,
        return_id: UUID,
    ) -> TaxReturn:
        tax_return = await self._require_return(return_id)

        if tax_return.status != "draft":
            raise TaxFilingError("Tax return is not draft")

        if tax_return.created_by == self.user_id:
            raise TaxFilingError("Creator cannot approve the same tax return")

        tax_return.status = "approved"
        tax_return.approved_by = self.user_id

        await self.db.commit()
        await self.db.refresh(tax_return)

        return tax_return

    async def remit(
        self,
        return_id: UUID,
        data: TaxRemittanceCreate,
    ) -> TaxRemittance:
        tax_return = await self._require_return(return_id)

        if tax_return.status not in {
            "approved",
            "filed",
        }:
            raise TaxFilingError("Tax return is not approved")

        liability_statement = select(TaxLiability).where(
            TaxLiability.id == data.liability_id,
            TaxLiability.tenant_id == self.tenant_id,
        )
        liability = await self.db.scalar(liability_statement)

        if liability is None:
            raise TaxFilingError("Tax liability was not found")

        if data.amount > liability.open_amount:
            raise TaxFilingError("Remittance exceeds open liability")

        remittance = TaxRemittance(
            tenant_id=self.tenant_id,
            tax_return_id=tax_return.id,
            payment_date=data.payment_date,
            amount=data.amount,
        )
        self.db.add(remittance)
        await self.db.flush()

        journal = JournalEntry(
            tenant_id=self.tenant_id,
            ledger_id=data.ledger_id,
            period_id=data.accounting_period_id,
            journal_number=(f"TAX-{str(remittance.id)[:8]}"),
            journal_date=data.payment_date,
            description="Tax remittance",
            status="posted",
            created_by=self.user_id,
            approved_by=self.user_id,
            posted_at=datetime.now(UTC),
        )
        self.db.add(journal)
        await self.db.flush()

        self.db.add_all(
            [
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=journal.id,
                    line_number=1,
                    account_id=(data.tax_payable_account_id),
                    description="Clear tax payable",
                    debit=data.amount,
                    credit=Decimal("0"),
                    currency_code=data.currency_code,
                ),
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=journal.id,
                    line_number=2,
                    account_id=data.cash_account_id,
                    description="Tax payment cash",
                    debit=Decimal("0"),
                    credit=data.amount,
                    currency_code=data.currency_code,
                ),
                TaxRemittanceAllocation(
                    tenant_id=self.tenant_id,
                    remittance_id=remittance.id,
                    liability_id=liability.id,
                    amount=data.amount,
                ),
            ]
        )

        remittance.journal_id = journal.id
        liability.open_amount -= data.amount

        liability.status = "paid" if liability.open_amount == 0 else "partially_paid"
        tax_return.status = "filed"

        await self.db.commit()
        await self.db.refresh(remittance)

        return remittance

    async def notice(
        self,
        data: TaxNoticeCreate,
    ) -> TaxNotice:
        notice = TaxNotice(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(notice)

        await self.db.commit()
        await self.db.refresh(notice)

        return notice

    async def resolve_notice(
        self,
        notice_id: UUID,
        resolution: str,
    ) -> TaxNotice:
        notice_statement = select(TaxNotice).where(
            TaxNotice.id == notice_id,
            TaxNotice.tenant_id == self.tenant_id,
        )
        notice = await self.db.scalar(notice_statement)

        if notice is None:
            raise TaxFilingError("Tax notice was not found")

        notice.status = "resolved"
        notice.resolution = resolution

        await self.db.commit()
        await self.db.refresh(notice)

        return notice

    async def reconcile(
        self,
        authority_id: UUID,
        tax_payable_account_id: UUID,
    ) -> TaxReconciliationRun:
        liability_statement = select(TaxLiability).where(
            TaxLiability.tenant_id == self.tenant_id,
            TaxLiability.authority_id == authority_id,
        )
        liabilities = list((await self.db.scalars(liability_statement)).all())

        subledger_total = sum(
            (liability.open_amount for liability in liabilities),
            Decimal("0"),
        )

        line_statement = (
            select(JournalLine)
            .join(
                JournalEntry,
                JournalEntry.id == JournalLine.journal_id,
            )
            .where(
                JournalEntry.tenant_id == self.tenant_id,
                JournalLine.account_id == tax_payable_account_id,
            )
        )
        journal_lines = list((await self.db.scalars(line_statement)).all())

        gl_total = sum(
            (line.credit - line.debit for line in journal_lines),
            Decimal("0"),
        )

        reconciliation = TaxReconciliationRun(
            tenant_id=self.tenant_id,
            authority_id=authority_id,
            subledger_total=subledger_total,
            gl_total=gl_total,
            status=("reconciled" if subledger_total == gl_total else "exception"),
        )
        self.db.add(reconciliation)

        await self.db.commit()
        await self.db.refresh(reconciliation)

        return reconciliation

    async def _require_return(
        self,
        return_id: UUID,
    ) -> TaxReturn:
        return_statement = select(TaxReturn).where(
            TaxReturn.id == return_id,
            TaxReturn.tenant_id == self.tenant_id,
        )
        tax_return = await self.db.scalar(return_statement)

        if tax_return is None:
            raise TaxFilingError("Tax return was not found")

        return tax_return

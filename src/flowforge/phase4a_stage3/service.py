from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase2b.models import JournalEntry, JournalLine
from flowforge.phase4a.models import CompensationRate, WorkerProfile

from .calculator import calculate_payroll
from .models import (
    PayrollDeduction,
    PayrollEarning,
    PayrollLiability,
    PayrollPayment,
    PayrollReconciliationRun,
    PayrollRun,
    PayrollRunWorker,
    PayrollTaxLine,
)
from .schemas import PayrollCalculate, PayrollPaymentCreate, PayrollPostAccounts, PayrollRunCreate


class PayrollError(Exception):
    pass


class PayrollService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def create_run(
        self,
        data: PayrollRunCreate,
    ) -> PayrollRun:
        count_statement = (
            select(func.count())
            .select_from(PayrollRun)
            .where(PayrollRun.tenant_id == self.tenant_id)
        )
        count = await self.db.scalar(count_statement)

        payroll_run = PayrollRun(
            tenant_id=self.tenant_id,
            run_number=(f"PR-{int(count or 0) + 1:08d}"),
            created_by=self.user_id,
            **data.model_dump(),
        )
        self.db.add(payroll_run)

        await self.db.commit()
        await self.db.refresh(payroll_run)

        return payroll_run

    async def calculate(self, run_id: UUID, data: PayrollCalculate) -> PayrollRun:
        run = await self._run(run_id)
        if run.status != "draft":
            raise PayrollError("Only draft payroll can be calculated")
        for item in data.workers:
            worker = await self.db.scalar(
                select(WorkerProfile).where(
                    WorkerProfile.id == item.worker_id,
                    WorkerProfile.tenant_id == self.tenant_id,
                )
            )
            rate = await self.db.scalar(
                select(CompensationRate).where(
                    CompensationRate.worker_id == item.worker_id,
                    CompensationRate.tenant_id == self.tenant_id,
                    CompensationRate.compensation_type == "hourly",
                )
            )
            if worker is None or rate is None:
                raise PayrollError("Worker or hourly compensation was not found")
            result = calculate_payroll(
                item.regular_hours,
                item.overtime_hours,
                rate.amount,
                item.bonus,
                item.pretax_deductions,
                item.posttax_deductions,
                item.employee_tax_rate,
                item.employer_tax_rate,
            )
            payroll_worker = PayrollRunWorker(
                tenant_id=self.tenant_id,
                payroll_run_id=run.id,
                worker_id=worker.id,
                gross_pay=result.gross_pay,
                pretax_deductions=result.pretax_deductions,
                employee_taxes=result.employee_taxes,
                posttax_deductions=result.posttax_deductions,
                net_pay=result.net_pay,
                employer_taxes=result.employer_taxes,
            )
            self.db.add(payroll_worker)
            await self.db.flush()
            self.db.add_all(
                [
                    PayrollEarning(
                        tenant_id=self.tenant_id,
                        payroll_worker_id=payroll_worker.id,
                        earning_type="regular_and_overtime",
                        hours=item.regular_hours + item.overtime_hours,
                        rate=rate.amount,
                        amount=result.gross_pay,
                    ),
                    PayrollTaxLine(
                        tenant_id=self.tenant_id,
                        payroll_worker_id=payroll_worker.id,
                        tax_code="aggregate",
                        taxable_wages=result.taxable_wages,
                        employee_amount=result.employee_taxes,
                        employer_amount=result.employer_taxes,
                    ),
                ]
            )
            if result.pretax_deductions > 0:
                self.db.add(
                    PayrollDeduction(
                        tenant_id=self.tenant_id,
                        payroll_worker_id=payroll_worker.id,
                        deduction_type="pretax",
                        amount=result.pretax_deductions,
                        pretax=True,
                    )
                )
            if result.posttax_deductions > 0:
                self.db.add(
                    PayrollDeduction(
                        tenant_id=self.tenant_id,
                        payroll_worker_id=payroll_worker.id,
                        deduction_type="posttax",
                        amount=result.posttax_deductions,
                        pretax=False,
                    )
                )
        run.status = "calculated"
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def approve(self, run_id: UUID) -> PayrollRun:
        run = await self._run(run_id)
        if run.status != "calculated":
            raise PayrollError("Payroll is not ready for approval")
        if run.created_by == self.user_id:
            raise PayrollError("Payroll creator cannot approve the same run")
        run.status = "approved"
        run.approved_by = self.user_id
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def post(self, run_id: UUID, accounts: PayrollPostAccounts) -> PayrollRun:
        run = await self._run(run_id)
        if run.status != "approved":
            raise PayrollError("Payroll is not approved")
        workers = list(
            (
                await self.db.scalars(
                    select(PayrollRunWorker).where(PayrollRunWorker.payroll_run_id == run.id)
                )
            ).all()
        )
        gross = sum((x.gross_pay for x in workers), Decimal("0"))
        employer_tax = sum((x.employer_taxes for x in workers), Decimal("0"))
        employee_tax = sum((x.employee_taxes for x in workers), Decimal("0"))
        deductions = sum(
            (x.pretax_deductions + x.posttax_deductions for x in workers), Decimal("0")
        )
        net = sum((x.net_pay for x in workers), Decimal("0"))
        journal = JournalEntry(
            tenant_id=self.tenant_id,
            ledger_id=run.ledger_id,
            period_id=run.accounting_period_id,
            journal_number=f"PAYROLL-{run.run_number}",
            journal_date=datetime.now(UTC).date(),
            description=f"Payroll {run.run_number}",
            status="posted",
            created_by=self.user_id,
            approved_by=self.user_id,
            posted_at=datetime.now(UTC),
        )
        self.db.add(journal)
        await self.db.flush()
        lines = [
            (accounts.wage_expense_account_id, gross, Decimal("0"), "Gross wages"),
            (
                accounts.employer_tax_expense_account_id,
                employer_tax,
                Decimal("0"),
                "Employer payroll taxes",
            ),
            (
                accounts.employee_tax_payable_account_id,
                Decimal("0"),
                employee_tax,
                "Employee tax payable",
            ),
            (
                accounts.employer_tax_payable_account_id,
                Decimal("0"),
                employer_tax,
                "Employer tax payable",
            ),
            (
                accounts.deductions_payable_account_id,
                Decimal("0"),
                deductions,
                "Deductions payable",
            ),
            (
                accounts.net_pay_payable_account_id,
                Decimal("0"),
                net,
                "Net pay payable",
            ),
        ]
        for number, (account_id, debit, credit, description) in enumerate(lines, start=1):
            if debit == 0 and credit == 0:
                continue
            self.db.add(
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=journal.id,
                    line_number=number,
                    account_id=account_id,
                    description=description,
                    debit=debit,
                    credit=credit,
                    currency_code=accounts.currency_code,
                )
            )
        self.db.add_all(
            [
                PayrollLiability(
                    tenant_id=self.tenant_id,
                    payroll_run_id=run.id,
                    liability_type="net_pay",
                    amount=net,
                    open_amount=net,
                ),
                PayrollLiability(
                    tenant_id=self.tenant_id,
                    payroll_run_id=run.id,
                    liability_type="employee_tax",
                    amount=employee_tax,
                    open_amount=employee_tax,
                ),
                PayrollLiability(
                    tenant_id=self.tenant_id,
                    payroll_run_id=run.id,
                    liability_type="employer_tax",
                    amount=employer_tax,
                    open_amount=employer_tax,
                ),
            ]
        )
        run.status = "posted"
        run.posted_journal_id = journal.id
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def pay_worker(self, run_id: UUID, data: PayrollPaymentCreate) -> PayrollPayment:
        run = await self._run(run_id)
        if run.status not in {"posted", "funded", "paid"}:
            raise PayrollError("Payroll is not posted")
        payment = PayrollPayment(
            tenant_id=self.tenant_id,
            payroll_run_id=run.id,
            worker_id=data.worker_id,
            amount=data.amount,
            status="paid",
        )
        self.db.add(payment)
        await self.db.flush()
        journal = JournalEntry(
            tenant_id=self.tenant_id,
            ledger_id=run.ledger_id,
            period_id=run.accounting_period_id,
            journal_number=f"PAY-{str(payment.id)[:8]}",
            journal_date=datetime.now(UTC).date(),
            description="Payroll payment",
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
                    account_id=data.net_pay_payable_account_id,
                    description="Clear net pay",
                    debit=data.amount,
                    credit=Decimal("0"),
                    currency_code=data.currency_code,
                ),
                JournalLine(
                    tenant_id=self.tenant_id,
                    journal_id=journal.id,
                    line_number=2,
                    account_id=data.cash_account_id,
                    description="Payroll cash",
                    debit=Decimal("0"),
                    credit=data.amount,
                    currency_code=data.currency_code,
                ),
            ]
        )
        payment.journal_id = journal.id
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def reconcile(self, run_id: UUID) -> PayrollReconciliationRun:
        run = await self._run(run_id)
        workers = list(
            (
                await self.db.scalars(
                    select(PayrollRunWorker).where(PayrollRunWorker.payroll_run_id == run.id)
                )
            ).all()
        )
        subledger = sum((x.gross_pay + x.employer_taxes for x in workers), Decimal("0"))
        journal_lines = list(
            (
                await self.db.scalars(
                    select(JournalLine).where(JournalLine.journal_id == run.posted_journal_id)
                )
            ).all()
        )
        gl_total = sum((x.debit for x in journal_lines), Decimal("0"))
        item = PayrollReconciliationRun(
            tenant_id=self.tenant_id,
            payroll_run_id=run.id,
            subledger_total=subledger,
            gl_total=gl_total,
            status="reconciled" if subledger == gl_total else "exception",
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def _run(self, run_id: UUID) -> PayrollRun:
        run = await self.db.scalar(
            select(PayrollRun).where(
                PayrollRun.id == run_id,
                PayrollRun.tenant_id == self.tenant_id,
            )
        )
        if run is None:
            raise PayrollError("Payroll run not found")
        return run

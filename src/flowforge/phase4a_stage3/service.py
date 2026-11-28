from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase2b.models import JournalLine
from flowforge.phase2b.posting import PostingError, PostingLine, post_system_journal
from flowforge.phase4a.models import CompensationRate, WorkerProfile
from flowforge.phase4a_stage2.models import PayPeriod
from flowforge.platform.numbering import next_number

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

ANNUAL_HOURS = Decimal("2080")
PERIODS_PER_YEAR = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12}


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

        payroll_run = PayrollRun(
            tenant_id=self.tenant_id,
            run_number=await next_number(self.db, self.tenant_id, "payroll_run"),
            created_by=self.user_id,
            **data.model_dump(),
        )
        self.db.add(payroll_run)

        await self.db.commit()
        await self.db.refresh(payroll_run)

        return payroll_run

    async def _pay_basis(
        self, worker: WorkerProfile, regular_hours: Decimal
    ) -> tuple[Decimal | None, Decimal]:
        """Hourly rate and regular hours for a run: the current hourly rate, or for salaried
        workers the annual salary over 2,080 hours with the standard hours of their pay
        frequency when no hours are entered (gross = salary / pay periods per year)."""
        today = date.today()
        current = (
            select(CompensationRate)
            .where(
                CompensationRate.worker_id == worker.id,
                CompensationRate.tenant_id == self.tenant_id,
                CompensationRate.effective_from <= today,
                or_(
                    CompensationRate.effective_to.is_(None), CompensationRate.effective_to >= today
                ),
            )
            .order_by(CompensationRate.effective_from.desc())
        )
        any_date = (
            select(CompensationRate)
            .where(
                CompensationRate.worker_id == worker.id,
                CompensationRate.tenant_id == self.tenant_id,
            )
            .order_by(CompensationRate.effective_from.desc())
        )

        async def rate_of(kind: str) -> CompensationRate | None:
            # The rate in effect today; else the latest one (runs for past or future periods).
            found = await self.db.scalar(current.where(CompensationRate.compensation_type == kind))
            return found or await self.db.scalar(
                any_date.where(CompensationRate.compensation_type == kind)
            )

        hourly = await rate_of("hourly")
        if hourly is not None:
            return hourly.amount, regular_hours
        salary = await rate_of("salary")
        if salary is None:
            return None, regular_hours
        if regular_hours == 0:
            # A salaried period: exactly salary / periods, shown over the period's standard hours.
            periods = PERIODS_PER_YEAR.get(worker.pay_frequency, 26)
            regular_hours = (ANNUAL_HOURS / periods).quantize(Decimal("0.01"))
            period_pay = salary.amount / periods
            return (period_pay / regular_hours).quantize(Decimal("0.000001")), regular_hours
        return (salary.amount / ANNUAL_HOURS).quantize(Decimal("0.000001")), regular_hours

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
            hourly_rate, regular_hours = (
                await self._pay_basis(worker, item.regular_hours)
                if worker
                else (None, item.regular_hours)
            )
            if worker is None or hourly_rate is None:
                raise PayrollError("Worker or current hourly or salary compensation was not found")
            result = calculate_payroll(
                regular_hours,
                item.overtime_hours,
                hourly_rate,
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
                        hours=regular_hours + item.overtime_hours,
                        rate=hourly_rate,
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
        period = await self.db.get(PayPeriod, run.pay_period_id)
        if period is None:
            raise PayrollError("Pay period was not found")
        try:
            journal = await post_system_journal(
                self.db,
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                ledger_id=run.ledger_id,
                period_id=run.accounting_period_id,
                journal_number=f"PAYROLL-{run.run_number}",
                journal_date=period.pay_date,
                description=f"Payroll {run.run_number}",
                currency_code=accounts.currency_code,
                lines=[
                    PostingLine(
                        accounts.wage_expense_account_id, gross, Decimal("0"), "Gross wages"
                    ),
                    PostingLine(
                        accounts.employer_tax_expense_account_id,
                        employer_tax,
                        Decimal("0"),
                        "Employer payroll taxes",
                    ),
                    PostingLine(
                        accounts.employee_tax_payable_account_id,
                        Decimal("0"),
                        employee_tax,
                        "Employee tax payable",
                    ),
                    PostingLine(
                        accounts.employer_tax_payable_account_id,
                        Decimal("0"),
                        employer_tax,
                        "Employer tax payable",
                    ),
                    PostingLine(
                        accounts.deductions_payable_account_id,
                        Decimal("0"),
                        deductions,
                        "Deductions payable",
                    ),
                    PostingLine(
                        accounts.net_pay_payable_account_id, Decimal("0"), net, "Net pay payable"
                    ),
                ],
            )
        except PostingError as exc:
            raise PayrollError(str(exc)) from exc
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
        run_worker = await self.db.scalar(
            select(PayrollRunWorker).where(
                PayrollRunWorker.payroll_run_id == run.id,
                PayrollRunWorker.worker_id == data.worker_id,
                PayrollRunWorker.tenant_id == self.tenant_id,
            )
        )
        if run_worker is None:
            raise PayrollError("Worker is not part of this payroll run")
        already_paid = await self.db.scalar(
            select(func.coalesce(func.sum(PayrollPayment.amount), 0)).where(
                PayrollPayment.payroll_run_id == run.id,
                PayrollPayment.worker_id == data.worker_id,
                PayrollPayment.tenant_id == self.tenant_id,
            )
        )
        if Decimal(already_paid or 0) + data.amount > run_worker.net_pay:
            raise PayrollError("Payment exceeds the worker's unpaid net pay")
        liability = await self.db.scalar(
            select(PayrollLiability)
            .where(
                PayrollLiability.payroll_run_id == run.id,
                PayrollLiability.tenant_id == self.tenant_id,
                PayrollLiability.liability_type == "net_pay",
            )
            .with_for_update()
        )
        if liability is None or data.amount > liability.open_amount:
            raise PayrollError("Payment exceeds the open net-pay liability")
        period = await self.db.get(PayPeriod, run.pay_period_id)
        if period is None:
            raise PayrollError("Pay period was not found")
        payment = PayrollPayment(
            tenant_id=self.tenant_id,
            payroll_run_id=run.id,
            worker_id=data.worker_id,
            amount=data.amount,
            status="paid",
        )
        self.db.add(payment)
        await self.db.flush()
        try:
            journal = await post_system_journal(
                self.db,
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                ledger_id=run.ledger_id,
                period_id=run.accounting_period_id,
                journal_number=f"PAY-{str(payment.id)[:8]}",
                journal_date=period.pay_date,
                description="Payroll payment",
                currency_code=data.currency_code,
                lines=[
                    PostingLine(
                        data.net_pay_payable_account_id, data.amount, Decimal("0"), "Clear net pay"
                    ),
                    PostingLine(data.cash_account_id, Decimal("0"), data.amount, "Payroll cash"),
                ],
            )
        except PostingError as exc:
            raise PayrollError(str(exc)) from exc
        payment.journal_id = journal.id
        liability.open_amount -= data.amount
        liability.status = "paid" if liability.open_amount == 0 else "partially_paid"
        if liability.open_amount == 0:
            run.status = "paid"
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

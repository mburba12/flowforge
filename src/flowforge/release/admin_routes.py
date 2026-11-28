"""Period close/reopen, tax authorities, and tax liabilities derived from posted payroll."""

from datetime import date
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase2b.models import AccountingPeriod, JournalEntry
from flowforge.phase4a_stage3.models import PayrollLiability, PayrollRun
from flowforge.phase4b.models import TaxAuthority, TaxJurisdiction
from flowforge.phase4b_stage2.models import TaxLiability
from flowforge.platform.services import record_change

router = APIRouter(tags=["release-admin"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


class ReopenRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class AuthorityCreate(BaseModel):
    jurisdiction_id: UUID
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)


class LiabilitiesFromPayroll(BaseModel):
    payroll_run_id: UUID
    authority_id: UUID
    due_date: date


def _period_view(p: AccountingPeriod) -> dict[str, Any]:
    return {
        "id": str(p.id),
        "calendar_id": str(p.calendar_id),
        "period_code": p.period_code,
        "start_date": p.start_date.isoformat(),
        "end_date": p.end_date.isoformat(),
        "status": p.status,
    }


async def _period(db: AsyncSession, tenant_id: UUID, period_id: UUID) -> AccountingPeriod:
    period = await db.scalar(
        select(AccountingPeriod)
        .where(AccountingPeriod.id == period_id, AccountingPeriod.tenant_id == tenant_id)
        .with_for_update()
    )
    if period is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Accounting period not found")
    return period


@router.get("/api/v2/accounting-periods")
async def list_periods(p: P, db: D) -> list[dict[str, Any]]:
    rows = (
        await db.scalars(
            select(AccountingPeriod)
            .where(AccountingPeriod.tenant_id == p.tenant_id)
            .order_by(AccountingPeriod.start_date)
        )
    ).all()
    return [_period_view(x) for x in rows]


@router.post("/api/v2/accounting-periods/{period_id}/close")
async def close_period(period_id: UUID, p: P, db: D) -> dict[str, Any]:
    period = await _period(db, p.tenant_id, period_id)
    if period.status != "open":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Period is {period.status}, not open")
    pending = await db.scalar(
        select(func.count())
        .select_from(JournalEntry)
        .where(
            JournalEntry.tenant_id == p.tenant_id,
            JournalEntry.period_id == period.id,
            JournalEntry.status.in_(("draft", "submitted", "approved")),
        )
    )
    if pending:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Period has {pending} unposted journal(s); post or reject them before closing",
        )
    period.status = "closed"
    await record_change(db, p.tenant_id, p.user_id, "closed", "accounting_period", str(period.id))
    await db.commit()
    return _period_view(period)


@router.post("/api/v2/accounting-periods/{period_id}/reopen")
async def reopen_period(period_id: UUID, body: ReopenRequest, p: P, db: D) -> dict[str, Any]:
    period = await _period(db, p.tenant_id, period_id)
    if period.status != "closed":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Only closed periods can reopen (period is {period.status})"
        )
    period.status = "open"
    await record_change(
        db,
        p.tenant_id,
        p.user_id,
        "reopened",
        "accounting_period",
        str(period.id),
        {"reason": body.reason},
    )
    await db.commit()
    return _period_view(period)


@router.get("/api/v4b/authorities")
async def list_authorities(p: P, db: D) -> list[dict[str, str]]:
    rows = (
        await db.scalars(
            select(TaxAuthority)
            .where(TaxAuthority.tenant_id == p.tenant_id)
            .order_by(TaxAuthority.code)
        )
    ).all()
    return [
        {"id": str(x.id), "code": x.code, "name": x.name, "jurisdiction_id": str(x.jurisdiction_id)}
        for x in rows
    ]


@router.post("/api/v4b/authorities", status_code=201)
async def create_authority(body: AuthorityCreate, p: P, db: D) -> dict[str, str]:
    jurisdiction = await db.scalar(
        select(TaxJurisdiction).where(
            TaxJurisdiction.id == body.jurisdiction_id,
            TaxJurisdiction.tenant_id == p.tenant_id,
            TaxJurisdiction.active.is_(True),
        )
    )
    if jurisdiction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Active jurisdiction was not found")
    duplicate = await db.scalar(
        select(TaxAuthority).where(
            TaxAuthority.tenant_id == p.tenant_id, TaxAuthority.code == body.code
        )
    )
    if duplicate is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tax authority code already exists")
    authority = TaxAuthority(
        tenant_id=p.tenant_id, jurisdiction_id=jurisdiction.id, code=body.code, name=body.name
    )
    db.add(authority)
    await db.flush()
    await record_change(db, p.tenant_id, p.user_id, "created", "tax_authority", str(authority.id))
    await db.commit()
    return {"id": str(authority.id), "code": authority.code, "name": authority.name}


@router.post("/api/v4b/liabilities/from-payroll", status_code=201)
async def liabilities_from_payroll(
    body: LiabilitiesFromPayroll, p: P, db: D
) -> list[dict[str, str]]:
    """Create employee- and employer-tax liabilities from a posted payroll run's totals."""
    run = await db.scalar(
        select(PayrollRun).where(
            PayrollRun.id == body.payroll_run_id, PayrollRun.tenant_id == p.tenant_id
        )
    )
    if run is None or run.status not in {"posted", "funded", "paid"}:
        raise HTTPException(status.HTTP_409_CONFLICT, "Payroll run is not posted")
    authority = await db.scalar(
        select(TaxAuthority).where(
            TaxAuthority.id == body.authority_id, TaxAuthority.tenant_id == p.tenant_id
        )
    )
    if authority is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tax authority not found")
    created: list[dict[str, str]] = []
    for liability_type in ("employee_tax", "employer_tax"):
        exists = await db.scalar(
            select(TaxLiability).where(
                TaxLiability.tenant_id == p.tenant_id,
                TaxLiability.payroll_run_id == run.id,
                TaxLiability.authority_id == authority.id,
                TaxLiability.liability_type == liability_type,
            )
        )
        if exists is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"{liability_type} liability already exists for this run"
            )
        amount = await db.scalar(
            select(func.coalesce(func.sum(PayrollLiability.amount), 0)).where(
                PayrollLiability.payroll_run_id == run.id,
                PayrollLiability.tenant_id == p.tenant_id,
                PayrollLiability.liability_type == liability_type,
            )
        )
        if not amount:
            continue
        liability = TaxLiability(
            tenant_id=p.tenant_id,
            authority_id=authority.id,
            payroll_run_id=run.id,
            liability_type=liability_type,
            amount=amount,
            open_amount=amount,
            due_date=body.due_date,
        )
        db.add(liability)
        await db.flush()
        created.append(
            {
                "id": str(liability.id),
                "liability_type": liability_type,
                "amount": str(liability.amount),
                "open_amount": str(liability.open_amount),
            }
        )
    if not created:
        raise HTTPException(status.HTTP_409_CONFLICT, "Payroll run has no tax amounts")
    await record_change(
        db, p.tenant_id, p.user_id, "liabilities_created", "payroll_run", str(run.id)
    )
    await db.commit()
    return created

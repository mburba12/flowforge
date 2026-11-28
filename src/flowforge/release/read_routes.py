"""Read models for the release scope: order status and history, open items, aging, payroll, tax."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase3a.models import APOpenItem
from flowforge.phase3b.models import (
    AROpenItem,
    CustomerInvoice,
    SalesOrder,
    SalesOrderLine,
    Shipment,
)
from flowforge.phase4a_stage3.models import (
    PayrollLiability,
    PayrollPayment,
    PayrollRun,
    PayrollRunWorker,
)
from flowforge.phase4b_stage2.models import TaxLiability, TaxReturn
from flowforge.release.models import SalesOrderStatusEvent

router = APIRouter(tags=["release-read"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]
Limit = Annotated[int, Query(ge=1, le=500)]

BUCKETS = ("current", "1-30", "31-60", "61-90", "90+")


def _money(value: Decimal | None) -> str:
    return str((value or Decimal("0")).quantize(Decimal("0.01")))


def _bucket(due: date, as_of: date) -> str:
    days = (as_of - due).days
    if days <= 0:
        return "current"
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def _aging(items: list[Any], party_attr: str, as_of: date) -> dict[str, Any]:
    totals = dict.fromkeys(BUCKETS, Decimal("0"))
    by_party: dict[str, dict[str, Decimal]] = {}
    for item in items:
        if item.open_amount <= 0:
            continue
        bucket = _bucket(item.due_date, as_of)
        totals[bucket] += item.open_amount
        party = str(getattr(item, party_attr))
        row = by_party.setdefault(party, dict.fromkeys(BUCKETS, Decimal("0")))
        row[bucket] += item.open_amount
    return {
        "as_of": as_of.isoformat(),
        "buckets": {k: _money(v) for k, v in totals.items()},
        "total_open": _money(sum(totals.values(), Decimal("0"))),
        "by_party": [
            {party_attr: k, **{b: _money(v) for b, v in row.items()}}
            for k, row in sorted(by_party.items())
        ],
    }


def _open_item_view(item: Any, party_attr: str) -> dict[str, str]:
    return {
        "id": str(item.id),
        party_attr: str(getattr(item, party_attr)),
        "invoice_id": str(item.invoice_id),
        "original_amount": _money(item.original_amount),
        "open_amount": _money(item.open_amount),
        "due_date": item.due_date.isoformat(),
        "status": item.status,
    }


def _today() -> date:
    return datetime.now(UTC).date()


# ---------------------------------------------------------------- AR / orders
@router.get("/api/v3b/orders")
async def list_orders(
    p: P,
    db: D,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Limit = 100,
) -> list[dict[str, str]]:
    query = select(SalesOrder).where(SalesOrder.tenant_id == p.tenant_id)
    if status_filter:
        query = query.where(SalesOrder.status == status_filter)
    rows = (await db.scalars(query.order_by(SalesOrder.order_number.desc()).limit(limit))).all()
    return [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "customer_id": str(o.customer_id),
            "order_date": o.order_date.isoformat(),
            "status": o.status,
            "total": _money(o.total_amount),
        }
        for o in rows
    ]


@router.get("/api/v3b/orders/{order_id}")
async def get_order(order_id: UUID, p: P, db: D) -> dict[str, Any]:
    order = await db.scalar(
        select(SalesOrder).where(SalesOrder.id == order_id, SalesOrder.tenant_id == p.tenant_id)
    )
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    lines = (
        await db.scalars(select(SalesOrderLine).where(SalesOrderLine.order_id == order.id))
    ).all()
    history = (
        await db.scalars(
            select(SalesOrderStatusEvent)
            .where(SalesOrderStatusEvent.order_id == order.id)
            .order_by(SalesOrderStatusEvent.changed_at, SalesOrderStatusEvent.id)
        )
    ).all()
    shipments = (await db.scalars(select(Shipment).where(Shipment.order_id == order.id))).all()
    invoices = (
        await db.scalars(select(CustomerInvoice).where(CustomerInvoice.order_id == order.id))
    ).all()
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "customer_id": str(order.customer_id),
        "order_date": order.order_date.isoformat(),
        "status": order.status,
        "total": _money(order.total_amount),
        "lines": [
            {
                "product_id": str(x.product_id),
                "quantity": str(x.quantity),
                "unit_price": _money(x.unit_price),
                "reserved": str(x.reserved_quantity),
                "shipped": str(x.shipped_quantity),
            }
            for x in lines
        ],
        "status_history": [
            {"status": e.status, "at": e.changed_at.isoformat(), "note": e.note} for e in history
        ],
        "shipments": [
            {"shipment_number": s.shipment_number, "ship_date": s.ship_date.isoformat()}
            for s in shipments
        ],
        "invoices": [
            {
                "invoice_number": i.invoice_number,
                "total": _money(i.total_amount),
                "status": i.status,
            }
            for i in invoices
        ],
    }


@router.get("/api/v3b/open-items")
async def ar_open_items(p: P, db: D, limit: Limit = 200) -> list[dict[str, str]]:
    rows = (
        await db.scalars(
            select(AROpenItem)
            .where(AROpenItem.tenant_id == p.tenant_id, AROpenItem.open_amount > 0)
            .order_by(AROpenItem.due_date)
            .limit(limit)
        )
    ).all()
    return [_open_item_view(x, "customer_id") for x in rows]


@router.get("/api/v3b/aging")
async def ar_aging(p: P, db: D, as_of: date | None = None) -> dict[str, Any]:
    rows = list(
        (await db.scalars(select(AROpenItem).where(AROpenItem.tenant_id == p.tenant_id))).all()
    )
    return _aging(rows, "customer_id", as_of or _today())


# ---------------------------------------------------------------- AP
@router.get("/api/v3/open-items")
async def ap_open_items(p: P, db: D, limit: Limit = 200) -> list[dict[str, str]]:
    rows = (
        await db.scalars(
            select(APOpenItem)
            .where(APOpenItem.tenant_id == p.tenant_id, APOpenItem.open_amount > 0)
            .order_by(APOpenItem.due_date)
            .limit(limit)
        )
    ).all()
    return [_open_item_view(x, "vendor_id") for x in rows]


@router.get("/api/v3/aging")
async def ap_aging(p: P, db: D, as_of: date | None = None) -> dict[str, Any]:
    rows = list(
        (await db.scalars(select(APOpenItem).where(APOpenItem.tenant_id == p.tenant_id))).all()
    )
    return _aging(rows, "vendor_id", as_of or _today())


# ---------------------------------------------------------------- payroll
@router.get("/api/v4a/payroll/runs/{run_id}")
async def get_payroll_run(run_id: UUID, p: P, db: D) -> dict[str, Any]:
    run = await db.scalar(
        select(PayrollRun).where(PayrollRun.id == run_id, PayrollRun.tenant_id == p.tenant_id)
    )
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payroll run not found")
    workers = (
        await db.scalars(select(PayrollRunWorker).where(PayrollRunWorker.payroll_run_id == run.id))
    ).all()
    liabilities = (
        await db.scalars(select(PayrollLiability).where(PayrollLiability.payroll_run_id == run.id))
    ).all()
    payments = (
        await db.scalars(select(PayrollPayment).where(PayrollPayment.payroll_run_id == run.id))
    ).all()

    def total(attr: str) -> str:
        return _money(sum((getattr(w, attr) for w in workers), Decimal("0")))

    return {
        "id": str(run.id),
        "run_number": run.run_number,
        "status": run.status,
        "workers": len(workers),
        "totals": {
            "gross": total("gross_pay"),
            "employee_taxes": total("employee_taxes"),
            "employer_taxes": total("employer_taxes"),
            "deductions": _money(
                sum((w.pretax_deductions + w.posttax_deductions for w in workers), Decimal("0"))
            ),
            "net": total("net_pay"),
        },
        "liabilities": [
            {"type": x.liability_type, "amount": _money(x.amount), "open": _money(x.open_amount)}
            for x in liabilities
        ],
        "paid": _money(sum((x.amount for x in payments), Decimal("0"))),
        "posted_journal_id": str(run.posted_journal_id) if run.posted_journal_id else None,
    }


# ---------------------------------------------------------------- tax
@router.get("/api/v4b/liabilities")
async def list_tax_liabilities(p: P, db: D, limit: Limit = 200) -> list[dict[str, str]]:
    rows = (
        await db.scalars(
            select(TaxLiability)
            .where(TaxLiability.tenant_id == p.tenant_id)
            .order_by(TaxLiability.due_date)
            .limit(limit)
        )
    ).all()
    return [
        {
            "id": str(x.id),
            "authority_id": str(x.authority_id),
            "payroll_run_id": str(x.payroll_run_id),
            "liability_type": x.liability_type,
            "amount": _money(x.amount),
            "open_amount": _money(x.open_amount),
            "due_date": x.due_date.isoformat(),
            "status": x.status,
        }
        for x in rows
    ]


@router.get("/api/v4b/returns")
async def list_tax_returns(p: P, db: D, limit: Limit = 200) -> list[dict[str, str]]:
    rows = (
        await db.scalars(
            select(TaxReturn)
            .where(TaxReturn.tenant_id == p.tenant_id)
            .order_by(TaxReturn.period_start.desc())
            .limit(limit)
        )
    ).all()
    return [
        {
            "id": str(x.id),
            "authority_id": str(x.authority_id),
            "period_code": x.period_code,
            "due_date": x.due_date.isoformat(),
            "total_tax": _money(x.total_tax),
            "status": x.status,
        }
        for x in rows
    ]

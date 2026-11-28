"""Background billing cycle, run inside the API every 15 minutes:

1. save the request counts gathered in memory to usage_days;
2. once a day, measure every workspace's storage (and bank accounts);
3. from the 1st of each month, issue last month's invoice to every billed workspace
   and email it to the workspace's owners;
4. charge invoices whose charge date (3 business days after the invoice) has come.

Every step is idempotent (unique invoice per workspace and month, Stripe idempotency
keys), and a database advisory lock keeps two API processes from running it at once.
"""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.config import settings
from flowforge.db.session import SessionLocal, engine
from flowforge.platform.models import Tenant

from . import invoices, metering
from .models import BillingInvoice

logger = logging.getLogger("flowforge.billing")
INTERVAL_SECONDS = 15 * 60
_LOCK_KEY = 7_311_024  # pg advisory lock id for the billing cycle
_state: dict[str, date | None] = {"snapshot": None, "invoices": None}


def enabled() -> bool:
    choice = settings.billing.strip().lower()
    if choice in {"on", "true", "1", "yes"}:
        return True
    if choice in {"off", "false", "0", "no"}:
        return False
    return settings.env == "production"


# Background work acts for no person; RLS needs a user id in the context, so it uses this
# reserved id (no user row has it; nothing in the database references it).
SYSTEM_USER = UUID(int=0)


def _session(tenant_id: UUID) -> AsyncSession:
    session = SessionLocal()
    session.info["tenant_id"] = tenant_id
    session.info["user_id"] = SYSTEM_USER
    return session


async def _tenants() -> list[Tenant]:
    async with SessionLocal() as db:
        return list(
            (
                await db.scalars(
                    select(Tenant).where(Tenant.is_deleted.is_(False), Tenant.status == "active")
                )
            ).all()
        )


async def flush_requests() -> int:
    """Save the in-memory request counts. Counts of workspaces that no longer exist are
    dropped; a workspace that fails to save keeps its counts for the next cycle."""
    counts = metering.take_counts()
    saved = 0
    live = {tenant.id for tenant in await _tenants()}
    by_tenant: dict[UUID, list[tuple[date, int]]] = {}
    for (tenant_id, day), n in counts.items():
        by_tenant.setdefault(tenant_id, []).append((day, n))
    keep: dict[tuple[UUID, date], int] = {}
    for tenant_id, days in by_tenant.items():
        if tenant_id not in live:
            continue  # deleted workspace: nothing to bill
        try:
            async with _session(tenant_id) as db:
                for day, n in days:
                    await metering.add_requests(db, tenant_id, day, n)
                await db.commit()
        except SQLAlchemyError:
            logger.exception(
                "Could not save usage for workspace %s; retrying next cycle", tenant_id
            )
            keep.update({(tenant_id, day): n for day, n in days})
            continue
        saved += sum(n for _, n in days)
    metering.restore_counts(keep)
    return saved


async def snapshot_storage(day: date) -> int:
    async with SessionLocal() as db:
        sizes = await metering.storage_by_tenant(db)
    measured = 0
    for tenant in await _tenants():
        async with _session(tenant.id) as db:
            banks = await metering.bank_account_count(db, tenant.id)
            await metering.record_snapshot(db, tenant.id, day, sizes.get(tenant.id, 0), banks)
            await db.commit()
        measured += 1
    return measured


async def issue_invoices(today: date) -> int:
    start, end = invoices.previous_month(today)
    issued = 0
    for tenant in await _tenants():
        if invoices.exempt(tenant):
            continue
        async with _session(tenant.id) as db:
            invoice = await invoices.issue_invoice(db, tenant, start, end, today)
            if invoice is None:
                continue
            await db.commit()
            await invoices.email_invoice(db, invoice, tenant)
            await db.commit()
            issued += 1
            logger.info("Invoice %s issued to %s: %s", invoice.number, tenant.slug, invoice.total)
    return issued


async def charge_due(today: date) -> int:
    charged = 0
    for tenant in await _tenants():
        if invoices.exempt(tenant):
            continue
        async with _session(tenant.id) as db:
            due = (
                await db.scalars(
                    select(BillingInvoice).where(
                        BillingInvoice.tenant_id == tenant.id,
                        BillingInvoice.status.in_(("open", "failed")),
                        BillingInvoice.charge_on <= today,
                    )
                )
            ).all()
            for invoice in due:
                await invoices.charge_invoice(db, invoice, tenant)
                await db.commit()
                charged += invoice.status == "paid"
    return charged


async def run_cycle(now: datetime | None = None) -> dict[str, int]:
    """One billing cycle (also used by tests and the manual "run billing now" action)."""
    moment = now or datetime.now(UTC)
    today = moment.date()
    result = {"requests": 0, "measured": 0, "issued": 0, "charged": 0}
    async with engine.connect() as lock_conn:
        got = await lock_conn.scalar(text("SELECT pg_try_advisory_lock(:k)"), {"k": _LOCK_KEY})
        if not got:
            return result
        try:
            result["requests"] = await flush_requests()
            if _state["snapshot"] != today:
                result["measured"] = await snapshot_storage(today)
                _state["snapshot"] = today
            if _state["invoices"] != today:
                result["issued"] = await issue_invoices(today)
                _state["invoices"] = today
            result["charged"] = await charge_due(today)
        finally:
            await lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _LOCK_KEY})
            await lock_conn.commit()
    return result


def reset_state() -> None:
    _state["snapshot"] = None
    _state["invoices"] = None


async def run_forever() -> None:
    await asyncio.sleep(30)  # let the API finish starting
    while True:
        try:
            result = await run_cycle()
            if any(result.values()):
                logger.info("Billing cycle: %s", result)
        except Exception:  # noqa: BLE001 - keep billing alive; the next cycle retries
            logger.exception("Billing cycle failed")
        await asyncio.sleep(INTERVAL_SECONDS)


@contextlib.asynccontextmanager
async def running() -> AsyncIterator[None]:
    task = asyncio.create_task(run_forever()) if enabled() else None
    try:
        yield
    finally:
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

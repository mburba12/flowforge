"""Monthly invoices: usage for the month, priced; emailed to the workspace's owners; the
saved card is charged automatically 3 business days later."""

import html
from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.config import settings
from flowforge.platform.models import Role, Tenant, User, UserRole

from . import mailer, stripe
from .models import BillingAccount, BillingInvoice, UsageDay
from .pricing import GB, Usage, add_business_days, quote

CHARGE_AFTER_BUSINESS_DAYS = 3
MAX_CHARGE_ATTEMPTS = 3


def previous_month(day: date) -> tuple[date, date]:
    end = day.replace(day=1) - timedelta(days=1)
    return end.replace(day=1), end


def month_bounds(day: date) -> tuple[date, date]:
    return day.replace(day=1), day.replace(day=monthrange(day.year, day.month)[1])


async def usage_for(db: AsyncSession, tenant_id: UUID, start: date, end: date) -> Usage:
    """Average storage and bank accounts over the month (last measurement carried forward
    over days that were not measured) and the month's billable requests."""
    rows = (
        await db.scalars(
            select(UsageDay)
            .where(UsageDay.tenant_id == tenant_id, UsageDay.day <= end)
            .order_by(UsageDay.day)
        )
    ).all()
    before = [r for r in rows if r.day < start and r.measured_at is not None]
    by_day = {r.day: r for r in rows if r.day >= start}
    storage = before[-1].storage_bytes if before else 0
    banks = before[-1].bank_accounts if before else 0
    storage_total = 0
    bank_total = 0
    requests = 0
    days = (end - start).days + 1
    for offset in range(days):
        row = by_day.get(start + timedelta(days=offset))
        if row is not None:
            requests += row.requests
            if row.measured_at is not None:
                storage, banks = row.storage_bytes, row.bank_accounts
        storage_total += storage
        bank_total += banks
    return Usage(
        storage_gb_months=Decimal(storage_total) / GB / days,
        requests=requests,
        bank_account_months=Decimal(bank_total) / days,
    )


async def owner_emails(db: AsyncSession, tenant_id: UUID) -> list[str]:
    rows = await db.scalars(
        select(User.email)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(
            User.tenant_id == tenant_id,
            Role.name == "Owner",
            User.is_active.is_(True),
            User.is_deleted.is_(False),
        )
    )
    return sorted({e for e in rows if e})


def exempt(tenant: Tenant) -> bool:
    return tenant.slug in {s.strip() for s in settings.billing_exempt.split(",") if s.strip()}


async def issue_invoice(
    db: AsyncSession, tenant: Tenant, start: date, end: date, issued: date
) -> BillingInvoice | None:
    """Create the month's invoice once (None if it exists or there was no usage)."""
    existing = await db.scalar(
        select(BillingInvoice).where(
            BillingInvoice.tenant_id == tenant.id, BillingInvoice.period_start == start
        )
    )
    if existing is not None:
        return None
    has_usage = await db.scalar(
        select(UsageDay.id)
        .where(UsageDay.tenant_id == tenant.id, UsageDay.day >= start, UsageDay.day <= end)
        .limit(1)
    )
    if has_usage is None:
        return None
    priced = quote(await usage_for(db, tenant.id, start, end))
    invoice = BillingInvoice(
        tenant_id=tenant.id,
        number=f"KWA-{start:%Y%m}-{str(tenant.id)[:6].upper()}",
        period_start=start,
        period_end=end,
        currency=priced["currency"],
        lines=priced["lines"],
        cost_basis=Decimal(priced["cost_basis"]),
        total=Decimal(priced["total"]),
        status="open",
        charge_on=add_business_days(issued, CHARGE_AFTER_BUSINESS_DAYS),
    )
    db.add(invoice)
    await db.flush()
    return invoice


def _money(value: Decimal | str) -> str:
    return f"${Decimal(value):,.2f}"


def _long(day: date) -> str:
    return f"{day:%A}, {day:%B} {day.day}, {day.year}"


def invoice_email(
    invoice: BillingInvoice, tenant: Tenant, account: BillingAccount | None
) -> tuple[str, str, str]:
    """Subject, plain text and HTML of the invoice email."""
    period = f"{invoice.period_start:%B %Y}"
    charge_day = _long(invoice.charge_on)
    if account and account.payment_method_id:
        card = f"{(account.card_brand or 'card').title()} ending in {account.card_last4}"
        payment = (
            f"Your {card} will be charged {_money(invoice.total)} automatically on {charge_day}, "
            f"3 business days from the date of this invoice. You do not need to do anything."
        )
    else:
        payment = (
            f"There is no card on file. Please add one in Krov WorkAgent (Settings, then Billing & usage) "
            f"before {charge_day}; it will be charged {_money(invoice.total)} automatically on that day."
        )
    subject = f"Krov WorkAgent invoice {invoice.number} for {period}: {_money(invoice.total)}"
    rows = [
        (line["description"], f"{line['quantity']} {line['unit']}", _money(line["amount"]))
        for line in invoice.lines
    ]
    text_lines = [
        f"Krov WorkAgent invoice {invoice.number}",
        f"Workspace: {tenant.name}",
        f"Period: {invoice.period_start:%B %d, %Y} to {invoice.period_end:%B %d, %Y}",
        f"Invoice date: {invoice.issued_at:%B %d, %Y}" if invoice.issued_at else "",
        "",
        *[f"  {d}: {q} = {a}" for d, q, a in rows],
        "",
        f"Total due: {_money(invoice.total)} ({invoice.currency.upper()})",
        "",
        payment,
        "",
        "You pay only for what you use: storage and activity. Moving your data in and keeping it in sync are free.",
        "Questions? Reply to this email.",
    ]
    table = "".join(
        f"<tr><td style='padding:6px 0'>{html.escape(d)}</td><td style='padding:6px 12px;color:#555'>{html.escape(q)}</td>"
        f"<td style='padding:6px 0;text-align:right'>{a}</td></tr>"
        for d, q, a in rows
    )
    html_body = f"""<div style="font-family:Segoe UI,Arial,sans-serif;max-width:560px;color:#0f172a">
<h2 style="margin:0 0 4px">Krov WorkAgent</h2>
<p style="margin:0 0 16px;color:#555">Invoice {html.escape(invoice.number)} &middot; {html.escape(tenant.name)}</p>
<p>Usage from {invoice.period_start:%B %d, %Y} to {invoice.period_end:%B %d, %Y}.</p>
<table style="width:100%;border-collapse:collapse;border-top:1px solid #ddd;border-bottom:1px solid #ddd">{table}</table>
<p style="font-size:18px"><b>Total due: {_money(invoice.total)}</b> ({invoice.currency.upper()})</p>
<p style="background:#f1f5f9;padding:12px;border-radius:8px"><b>{html.escape(payment)}</b></p>
<p style="color:#555;font-size:13px">You pay only for what you use: storage and activity. Moving your data in and keeping it in sync are free.</p>
</div>"""
    return subject, "\n".join(line for line in text_lines if line is not None), html_body


async def email_invoice(db: AsyncSession, invoice: BillingInvoice, tenant: Tenant) -> None:
    recipients = await owner_emails(db, tenant.id)
    account = await db.scalar(select(BillingAccount).where(BillingAccount.tenant_id == tenant.id))
    subject, text_body, html_body = invoice_email(invoice, tenant, account)
    invoice.emailed_to = ", ".join(recipients)
    if not recipients:
        invoice.email_error = "No active owner with an email address."
        return
    try:
        result = await mailer.send(recipients, subject, text_body, html_body)
    except mailer.MailNotSent as exc:
        invoice.email_error = str(exc)
        return
    invoice.emailed_at = datetime.now(UTC)
    invoice.email_error = (
        None if result == "sent" else "Kept in the mail outbox (SMTP not configured)."
    )


async def charge_invoice(db: AsyncSession, invoice: BillingInvoice, tenant: Tenant) -> None:
    """Charge the saved card for an invoice that is due."""
    account = await db.scalar(select(BillingAccount).where(BillingAccount.tenant_id == tenant.id))
    if not account or not account.payment_method_id or not account.stripe_customer_id:
        invoice.last_error = "No card on file."
        return
    invoice.charge_attempts += 1
    try:
        result = await stripe.charge(
            account.stripe_customer_id,
            account.payment_method_id,
            Decimal(invoice.total),
            f"Krov WorkAgent {invoice.number}",
            f"{invoice.id}-{invoice.charge_attempts}",
        )
    except stripe.StripeError as exc:
        invoice.last_error = str(exc)
        invoice.payment_intent_id = exc.payment_intent or invoice.payment_intent_id
        invoice.status = (
            "uncollected" if invoice.charge_attempts >= MAX_CHARGE_ATTEMPTS else "failed"
        )
        if invoice.status == "failed":  # retry on the next business day
            invoice.charge_on = add_business_days(datetime.now(UTC).date(), 1)
        await _email_failure(db, invoice, tenant, str(exc))
        return
    invoice.status = "paid"
    invoice.charged_at = datetime.now(UTC)
    invoice.payment_intent_id = str(result.get("id"))
    invoice.last_error = None


async def _email_failure(
    db: AsyncSession, invoice: BillingInvoice, tenant: Tenant, reason: str
) -> None:
    recipients = await owner_emails(db, tenant.id)
    if not recipients:
        return
    retry = (
        f"We will try again on {_long(invoice.charge_on)}."
        if invoice.status == "failed"
        else "Please update your card in Settings, then Billing & usage, and pay the invoice there."
    )
    text_body = (
        f"The automatic payment of {_money(invoice.total)} for invoice {invoice.number} did not go through: "
        f"{reason}\n\n{retry}"
    )
    try:
        await mailer.send(
            recipients,
            f"Payment failed for Krov WorkAgent invoice {invoice.number}",
            text_body,
            f"<p>{html.escape(text_body).replace(chr(10), '<br>')}</p>",
        )
    except mailer.MailNotSent:
        pass


def invoice_view(invoice: BillingInvoice) -> dict[str, Any]:
    return {
        "id": str(invoice.id),
        "number": invoice.number,
        "period_start": invoice.period_start.isoformat(),
        "period_end": invoice.period_end.isoformat(),
        "lines": invoice.lines,
        "total": str(invoice.total),
        "currency": invoice.currency,
        "status": invoice.status,
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "charge_on": invoice.charge_on.isoformat(),
        "emailed_to": invoice.emailed_to,
        "emailed_at": invoice.emailed_at.isoformat() if invoice.emailed_at else None,
        "email_error": invoice.email_error,
        "charged_at": invoice.charged_at.isoformat() if invoice.charged_at else None,
        "charge_attempts": invoice.charge_attempts,
        "last_error": invoice.last_error,
    }

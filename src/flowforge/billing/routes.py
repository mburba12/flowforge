"""Billing & usage for a workspace (its card, its usage, its invoices, the calculator) and
each person's screen preferences (sections they hid)."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.accounts.service import require_verified_email
from flowforge.core.config import settings
from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.platform.models import Tenant, User
from flowforge.platform.services import record_change

from . import invoices, mailer, stripe
from .models import BillingAccount, BillingInvoice, UserPreferences
from .pricing import Usage, current_rates, quote

router = APIRouter(prefix="/api/v1/account-billing", tags=["billing"])
prefs_router = APIRouter(prefix="/api/v1/me", tags=["preferences"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def _card(account: BillingAccount | None) -> dict[str, Any] | None:
    if not account or not account.payment_method_id:
        return None
    return {
        "brand": account.card_brand,
        "last4": account.card_last4,
        "exp_month": account.card_exp_month,
        "exp_year": account.card_exp_year,
        "authorized_at": account.authorized_at.isoformat() if account.authorized_at else None,
    }


async def _account(db: AsyncSession, tenant_id: UUID) -> BillingAccount | None:
    return await db.scalar(select(BillingAccount).where(BillingAccount.tenant_id == tenant_id))


@router.get("/summary")
async def summary(db: D, p: P) -> dict[str, Any]:
    tenant = await db.get(Tenant, p.tenant_id)
    today = datetime.now(UTC).date()
    start, end = invoices.month_bounds(today)
    so_far = await invoices.usage_for(db, p.tenant_id, start, today)
    elapsed = (today - start).days + 1
    days = (end - start).days + 1
    projected = Usage(
        storage_gb_months=so_far.storage_gb_months,
        requests=round(so_far.requests * days / elapsed),
        bank_account_months=so_far.bank_account_months,
    )
    rows = (
        await db.scalars(
            select(BillingInvoice)
            .where(BillingInvoice.tenant_id == p.tenant_id)
            .order_by(BillingInvoice.period_start.desc())
            .limit(24)
        )
    ).all()
    return {
        "exempt": bool(tenant and invoices.exempt(tenant)),
        "rates": current_rates().public(),
        "card": _card(await _account(db, p.tenant_id)),
        "month": {"start": start.isoformat(), "end": end.isoformat(), "today": today.isoformat()},
        "so_far": {
            "storage_gb": str(so_far.storage_gb_months.quantize(Decimal("0.0001"))),
            "requests": so_far.requests,
        },
        "estimate": quote(projected),
        "invoices": [invoices.invoice_view(i) for i in rows],
        "payments_ready": stripe.configured(),
        "email_ready": mailer.configured(),
        "charge_after_business_days": invoices.CHARGE_AFTER_BUSINESS_DAYS,
    }


class CalculatorInput(BaseModel):
    storage_gb: Decimal = Field(ge=0, le=100_000)
    requests: int = Field(ge=0, le=1_000_000_000)
    bank_accounts: Decimal = Field(default=Decimal(0), ge=0, le=10_000)


@router.post("/calculator")
async def calculator(body: CalculatorInput, p: P) -> dict[str, Any]:
    return quote(Usage(body.storage_gb, body.requests, body.bank_accounts))


class CardSetup(BaseModel):
    # The person agrees that the card is charged automatically for each monthly invoice.
    authorize_automatic_charges: bool


@router.post("/card")
async def add_card(body: CardSetup, db: D, p: P) -> dict[str, str]:
    if not body.authorize_automatic_charges:
        raise HTTPException(422, "Please agree to automatic monthly charges to save a card.")
    await require_verified_email(db, p.user_id)
    if not stripe.configured():
        raise HTTPException(409, "Card payments are not set up on this server yet.")
    tenant = await db.get(Tenant, p.tenant_id)
    user = await db.get(User, p.user_id)
    if tenant is None or user is None:
        raise HTTPException(404, "Workspace not found")
    account = await _account(db, p.tenant_id)
    if account is None:
        account = BillingAccount(tenant_id=p.tenant_id)
        db.add(account)
    try:
        if not account.stripe_customer_id:
            account.stripe_customer_id = await stripe.create_customer(
                user.email, tenant.name, str(tenant.id)
            )
        base = settings.public_url.rstrip("/")
        session = await stripe.card_setup_session(
            account.stripe_customer_id,
            f"{base}/billing/card?session_id={{CHECKOUT_SESSION_ID}}",
            f"{base}/modules/plan",
        )
    except stripe.StripeError as exc:
        raise HTTPException(502, str(exc)) from exc
    account.pending_checkout_session = session["id"]
    account.updated_at = datetime.now(UTC)
    await db.commit()
    return {"url": session["url"]}


class CardComplete(BaseModel):
    session_id: str = Field(min_length=8, max_length=120)


@router.post("/card/complete")
async def complete_card(body: CardComplete, db: D, p: P) -> dict[str, Any]:
    account = await _account(db, p.tenant_id)
    if (
        account is None
        or not account.stripe_customer_id
        or account.pending_checkout_session != body.session_id
    ):
        raise HTTPException(409, "This card setup was not started from this workspace.")
    try:
        card = await stripe.finish_card_setup(body.session_id, account.stripe_customer_id)
    except stripe.StripeError as exc:
        raise HTTPException(502, str(exc)) from exc
    account.payment_method_id = card.payment_method_id
    account.card_brand = card.brand
    account.card_last4 = card.last4
    account.card_exp_month = card.exp_month
    account.card_exp_year = card.exp_year
    account.authorized_at = datetime.now(UTC)
    account.authorized_by = p.user_id
    account.pending_checkout_session = None
    account.updated_at = datetime.now(UTC)
    await record_change(
        db, p.tenant_id, p.user_id, "card_saved", "billing_account", str(account.id)
    )
    await db.commit()
    return {"card": _card(account)}


@router.delete("/card")
async def remove_card(db: D, p: P) -> dict[str, str]:
    account = await _account(db, p.tenant_id)
    if account and account.payment_method_id:
        account.payment_method_id = None
        account.card_brand = account.card_last4 = None
        account.card_exp_month = account.card_exp_year = None
        account.updated_at = datetime.now(UTC)
        await record_change(
            db, p.tenant_id, p.user_id, "card_removed", "billing_account", str(account.id)
        )
        await db.commit()
    return {"status": "removed"}


@router.post("/invoices/{invoice_id}/pay")
async def pay_now(invoice_id: UUID, db: D, p: P) -> dict[str, Any]:
    invoice = await db.scalar(
        select(BillingInvoice).where(
            BillingInvoice.id == invoice_id, BillingInvoice.tenant_id == p.tenant_id
        )
    )
    if invoice is None:
        raise HTTPException(404, "Invoice not found")
    if invoice.status == "paid":
        raise HTTPException(409, "This invoice is already paid.")
    tenant = await db.get(Tenant, p.tenant_id)
    assert tenant is not None
    if invoice.status == "uncollected":
        invoice.charge_attempts = 0
    await invoices.charge_invoice(db, invoice, tenant)
    await db.commit()
    if invoice.status != "paid":
        raise HTTPException(402, invoice.last_error or "The payment did not go through.")
    return invoices.invoice_view(invoice)


# ------------------------------------------------------------------ preferences
class Preferences(BaseModel):
    hidden: list[str] = Field(default_factory=list, max_length=200)


@prefs_router.get("/preferences")
async def get_preferences(db: D, p: P) -> dict[str, Any]:
    row = await db.scalar(
        select(UserPreferences).where(
            UserPreferences.tenant_id == p.tenant_id, UserPreferences.user_id == p.user_id
        )
    )
    return {"hidden": list((row.data if row else {}).get("hidden", []))}


@prefs_router.put("/preferences")
async def put_preferences(body: Preferences, db: D, p: P) -> dict[str, Any]:
    hidden = sorted({h for h in body.hidden if isinstance(h, str) and 0 < len(h) <= 80})
    row = await db.scalar(
        select(UserPreferences).where(
            UserPreferences.tenant_id == p.tenant_id, UserPreferences.user_id == p.user_id
        )
    )
    if row is None:
        row = UserPreferences(tenant_id=p.tenant_id, user_id=p.user_id, data={})
        db.add(row)
    row.data = {**(row.data or {}), "hidden": hidden}
    row.updated_at = datetime.now(UTC)
    await db.commit()
    return {"hidden": hidden}

"""Stripe, over its REST API (no SDK): save a card with Checkout, charge it off-session.

Card numbers never reach Krov WorkAgent: the customer types them on Stripe's page and we
keep only Stripe ids, the brand, the last four digits and the expiry.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from flowforge.connect.http import client
from flowforge.core.config import settings

API = "https://api.stripe.com"


class StripeError(ValueError):
    """Stripe refused or failed; the message is safe to show."""

    def __init__(self, message: str, code: str | None = None, payment_intent: str | None = None):
        super().__init__(message)
        self.code = code
        self.payment_intent = payment_intent


def configured() -> bool:
    return bool(settings.stripe_secret_key)


async def _call(
    method: str, path: str, data: dict[str, Any] | None = None, idempotency_key: str | None = None
) -> Any:
    if not configured():
        raise StripeError("Card payments are not set up on this server yet (Stripe key missing).")
    headers = {"Authorization": f"Bearer {settings.stripe_secret_key}"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    try:
        async with client(API) as http:
            response = await http.request(method, path, data=data, headers=headers)
    except httpx.HTTPError as exc:
        raise StripeError(f"Could not reach Stripe: {type(exc).__name__}") from exc
    body = response.json() if response.content else {}
    if response.status_code >= 400:
        error = body.get("error", {}) if isinstance(body, dict) else {}
        intent = error.get("payment_intent", {}) if isinstance(error, dict) else {}
        raise StripeError(
            str(error.get("message") or f"Stripe refused the request ({response.status_code})")[
                :300
            ],
            code=error.get("decline_code") or error.get("code"),
            payment_intent=intent.get("id") if isinstance(intent, dict) else None,
        )
    return body


async def create_customer(email: str, name: str, tenant_id: str) -> str:
    body = await _call(
        "POST",
        "/v1/customers",
        {"email": email, "name": name, "metadata[tenant_id]": tenant_id},
        idempotency_key=f"customer-{tenant_id}",
    )
    return str(body["id"])


async def card_setup_session(customer_id: str, success_url: str, cancel_url: str) -> dict[str, str]:
    """A Stripe Checkout page (setup mode) where the customer saves a card."""
    body = await _call(
        "POST",
        "/v1/checkout/sessions",
        {
            "mode": "setup",
            "customer": customer_id,
            "currency": settings.billing_currency,
            "payment_method_types[]": "card",
            "success_url": success_url,
            "cancel_url": cancel_url,
        },
    )
    return {"id": str(body["id"]), "url": str(body["url"])}


@dataclass
class SavedCard:
    payment_method_id: str
    brand: str
    last4: str
    exp_month: int
    exp_year: int


async def finish_card_setup(session_id: str, customer_id: str) -> SavedCard:
    body = await _call(
        "GET", f"/v1/checkout/sessions/{session_id}?expand[]=setup_intent.payment_method"
    )
    if body.get("customer") != customer_id:
        raise StripeError("This card setup belongs to another account.")
    intent = body.get("setup_intent") or {}
    if not isinstance(intent, dict) or intent.get("status") != "succeeded":
        raise StripeError("The card was not saved. Please try again.")
    method = intent.get("payment_method") or {}
    card = method.get("card") or {}
    await _call(
        "POST",
        f"/v1/customers/{customer_id}",
        {"invoice_settings[default_payment_method]": method["id"]},
    )
    return SavedCard(
        payment_method_id=str(method["id"]),
        brand=str(card.get("brand") or "card"),
        last4=str(card.get("last4") or ""),
        exp_month=int(card.get("exp_month") or 0),
        exp_year=int(card.get("exp_year") or 0),
    )


async def charge(
    customer_id: str, payment_method_id: str, amount: Decimal, description: str, key: str
) -> dict[str, Any]:
    """Charge the saved card now (off-session). Raises StripeError if it is declined."""
    cents = int((amount * 100).to_integral_value())
    body = await _call(
        "POST",
        "/v1/payment_intents",
        {
            "amount": str(cents),
            "currency": settings.billing_currency,
            "customer": customer_id,
            "payment_method": payment_method_id,
            "off_session": "true",
            "confirm": "true",
            "description": description,
            "metadata[invoice]": key,
        },
        idempotency_key=f"charge-{key}",
    )
    if body.get("status") != "succeeded":
        raise StripeError(
            f"The payment did not complete (status {body.get('status')}).",
            payment_intent=body.get("id"),
        )
    return dict(body)

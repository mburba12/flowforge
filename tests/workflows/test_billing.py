"""Usage billing: prices at a 70% margin, monthly invoices emailed to owners, automatic
card charges 3 business days later (Stripe replaced by a mock), metering, preferences."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from flowforge.billing import metering, scheduler
from flowforge.billing.pricing import Usage, add_business_days, quote
from flowforge.connect import http as provider_http
from flowforge.core.config import settings

from .conftest import Harness


class FakeStripe:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, list[str]]]] = []
        self.decline = False

    def __call__(self, request: httpx.Request) -> httpx.Response:
        form = parse_qs(request.content.decode()) if request.content else {}
        path = request.url.path
        self.calls.append((request.method, path, form))
        assert request.headers["Authorization"] == "Bearer sk_test_fake"
        if path == "/v1/customers" and request.method == "POST":
            return httpx.Response(200, json={"id": "cus_123"})
        if path == "/v1/checkout/sessions":
            assert form["mode"] == ["setup"] and form["customer"] == ["cus_123"]
            return httpx.Response(
                200, json={"id": "cs_test_1", "url": "https://checkout.stripe.test/cs_test_1"}
            )
        if path == "/v1/checkout/sessions/cs_test_1":
            return httpx.Response(
                200,
                json={
                    "id": "cs_test_1",
                    "customer": "cus_123",
                    "setup_intent": {
                        "status": "succeeded",
                        "payment_method": {
                            "id": "pm_visa",
                            "card": {
                                "brand": "visa",
                                "last4": "4242",
                                "exp_month": 12,
                                "exp_year": 2030,
                            },
                        },
                    },
                },
            )
        if path == "/v1/customers/cus_123":
            return httpx.Response(200, json={"id": "cus_123"})
        if path == "/v1/payment_intents":
            assert form["off_session"] == ["true"] and form["confirm"] == ["true"]
            assert request.headers.get("Idempotency-Key", "").startswith("charge-")
            if self.decline:
                return httpx.Response(
                    402,
                    json={
                        "error": {
                            "message": "Your card was declined.",
                            "decline_code": "insufficient_funds",
                            "payment_intent": {"id": "pi_declined"},
                        }
                    },
                )
            return httpx.Response(200, json={"id": "pi_paid", "status": "succeeded"})
        return httpx.Response(404, json={"error": {"message": f"unexpected {path}"}})


@pytest.fixture
def stripe_mock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[FakeStripe]:
    fake = FakeStripe()
    provider_http.TRANSPORT = httpx.MockTransport(fake)
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "mail_outbox", str(tmp_path / "outbox"))
    monkeypatch.setattr(settings, "public_url", "https://app.example.test")
    scheduler.reset_state()
    yield fake
    provider_http.TRANSPORT = None
    scheduler.reset_state()


def test_prices_keep_a_70_percent_margin_after_card_fees() -> None:
    for usage in [
        Usage(Decimal("0.3"), 40_000, Decimal(0)),
        Usage(Decimal("5"), 900_000, Decimal(2)),
        Usage(Decimal(0), 0, Decimal(0)),
    ]:
        bill = quote(usage)
        total = Decimal(bill["total"])
        profit = total - Decimal(bill["cost_basis"]) - Decimal(bill["card_fee"])
        assert abs(profit / total - Decimal("0.70")) < Decimal("0.005"), bill
    small = quote(Usage(Decimal("0.3"), 40_000, Decimal(0)))
    assert small["total"] == "6.94"  # (0.3 x 2.00 + 40 x 0.0245 + 0.30) / 0.271
    # Data sync is free: bank connections are not a billed line by default.
    assert {line["code"] for line in small["lines"]} == {"storage", "requests", "processing"}


def test_three_business_days_skip_weekends_and_bank_holidays() -> None:
    assert add_business_days(date(2026, 11, 30), 3) == date(2026, 12, 3)  # Mon -> Thu
    assert add_business_days(date(2026, 12, 1), 3) == date(2026, 12, 4)  # Tue -> Fri
    assert add_business_days(date(2026, 12, 3), 3) == date(2026, 12, 8)  # over a weekend
    assert add_business_days(date(2026, 11, 25), 3) == date(2026, 12, 1)  # Thanksgiving
    assert add_business_days(date(2026, 12, 23), 3) == date(2026, 12, 29)  # Christmas


async def _seed_november(h: Harness) -> None:
    for day in range(1, 31):
        await h.sql(
            "INSERT INTO usage_days (tenant_id, day, storage_bytes, requests, bank_accounts, measured_at)"
            " VALUES (:t, :d, 300000000, 1000, 1, now())",
            t=h.tenant_id,
            d=date(2026, 11, day),
        )


async def test_month_end_invoice_email_and_automatic_charge(
    harness: Harness, stripe_mock: FakeStripe, tmp_path: Path
) -> None:
    h = harness
    await _seed_november(h)

    # The owner saves a card (after agreeing to automatic charges) through Stripe Checkout.
    await h.post(
        "/api/v1/account-billing/card", json={"authorize_automatic_charges": False}, expect=422
    )
    started = await h.post(
        "/api/v1/account-billing/card", json={"authorize_automatic_charges": True}
    )
    assert started["url"] == "https://checkout.stripe.test/cs_test_1"
    success = next(f for m, p, f in stripe_mock.calls if p == "/v1/checkout/sessions")[
        "success_url"
    ][0]
    assert success == "https://app.example.test/billing/card?session_id={CHECKOUT_SESSION_ID}"
    saved = await h.post("/api/v1/account-billing/card/complete", json={"session_id": "cs_test_1"})
    assert saved["card"]["last4"] == "4242"
    # A manager can see billing but not change the card.
    await h.call("GET", "/api/v1/account-billing/summary", as_approver=True)
    await h.post(
        "/api/v1/account-billing/card",
        json={"authorize_automatic_charges": True},
        as_approver=True,
        expect=403,
    )

    # December 1st: November's invoice is issued and emailed; nothing is charged yet.
    first = await scheduler.run_cycle(datetime(2026, 12, 1, 6, 0, tzinfo=UTC))
    assert first["charged"] == 0
    summary = await h.call("GET", "/api/v1/account-billing/summary")
    invoice = next(i for i in summary["invoices"] if i["period_start"] == "2026-11-01")
    assert invoice["status"] == "open"
    assert invoice["charge_on"] == "2026-12-04"
    expected = quote(Usage(Decimal("0.3"), 30_000, Decimal(1)))["total"]
    assert invoice["total"] == expected
    assert invoice["emailed_to"].startswith("owner-")

    mails = [
        p.read_text(encoding="utf-8", errors="replace") for p in (tmp_path / "outbox").glob("*.eml")
    ]
    mail = next(m for m in mails if invoice["number"] in m)
    assert "Visa ending in 4242" in mail
    assert "Friday, December 4, 2026" in mail
    assert "3 business days" in mail
    assert invoice["emailed_to"] in mail

    # Running again the same day never creates a second invoice.
    await scheduler.run_cycle(datetime(2026, 12, 1, 7, 0, tzinfo=UTC))
    again = await h.call("GET", "/api/v1/account-billing/summary")
    assert sum(1 for i in again["invoices"] if i["period_start"] == "2026-11-01") == 1

    # December 4th: the card is charged automatically.
    await scheduler.run_cycle(datetime(2026, 12, 4, 6, 0, tzinfo=UTC))
    paid = next(
        i
        for i in (await h.call("GET", "/api/v1/account-billing/summary"))["invoices"]
        if i["period_start"] == "2026-11-01"
    )
    assert paid["status"] == "paid"
    charge = next(f for m, p, f in stripe_mock.calls if p == "/v1/payment_intents")
    assert charge["amount"] == [str(int(Decimal(expected) * 100))]
    assert charge["customer"] == ["cus_123"] and charge["payment_method"] == ["pm_visa"]


async def test_declined_card_is_retried_then_left_for_the_owner(
    harness: Harness, stripe_mock: FakeStripe, tmp_path: Path
) -> None:
    h = harness
    await _seed_november(h)
    await h.post("/api/v1/account-billing/card", json={"authorize_automatic_charges": True})
    await h.post("/api/v1/account-billing/card/complete", json={"session_id": "cs_test_1"})
    stripe_mock.decline = True
    await scheduler.run_cycle(datetime(2026, 12, 1, 6, 0, tzinfo=UTC))
    await scheduler.run_cycle(datetime(2026, 12, 4, 6, 0, tzinfo=UTC))
    invoice = (await h.call("GET", "/api/v1/account-billing/summary"))["invoices"][0]
    assert invoice["status"] == "failed"
    assert "declined" in invoice["last_error"]
    failure_mails = [
        p
        for p in (tmp_path / "outbox").glob("*.json")
        if "Payment failed" in p.read_text(encoding="utf-8")
    ]
    assert failure_mails
    # The owner fixes the card and pays from the app.
    stripe_mock.decline = False
    paid = await h.post(f"/api/v1/account-billing/invoices/{invoice['id']}/pay")
    assert paid["status"] == "paid"


async def test_no_card_on_file_says_so_in_the_email(
    harness: Harness, stripe_mock: FakeStripe, tmp_path: Path
) -> None:
    h = harness
    await _seed_november(h)
    await scheduler.run_cycle(datetime(2026, 12, 1, 6, 0, tzinfo=UTC))
    mails = [
        p.read_text(encoding="utf-8", errors="replace") for p in (tmp_path / "outbox").glob("*.eml")
    ]
    summary = await h.call("GET", "/api/v1/account-billing/summary")
    number = summary["invoices"][0]["number"]
    mail = next(m for m in mails if number in m)
    assert "There is no card on file" in mail
    await scheduler.run_cycle(datetime(2026, 12, 4, 6, 0, tzinfo=UTC))
    after = (await h.call("GET", "/api/v1/account-billing/summary"))["invoices"][0]
    assert after["status"] == "open" and after["last_error"] == "No card on file."


async def test_requests_are_metered_but_imports_and_sync_are_free(harness: Harness) -> None:
    h = harness
    metering.take_counts()  # start clean
    for _ in range(3):
        await h.call("GET", "/api/v1/users")
    await h.call("GET", "/api/v1/connections/status")
    await h.call("GET", "/api/v1/me/preferences")
    counts = metering.take_counts()
    mine = {k: v for k, v in counts.items() if str(k[0]) == str(h.tenant_id)}
    assert sum(mine.values()) == 3
    metering.restore_counts(counts)
    saved = await scheduler.flush_requests()
    assert saved >= 3
    rows = await h.sql("SELECT sum(requests) FROM usage_days WHERE tenant_id = :t", t=h.tenant_id)
    assert rows[0][0] >= 3


async def test_calculator_and_preferences(harness: Harness) -> None:
    h = harness
    bill = await h.post(
        "/api/v1/account-billing/calculator", json={"storage_gb": "0.3", "requests": 40000}
    )
    assert bill["total"] == "6.94"
    assert (await h.call("GET", "/api/v1/me/preferences")) == {"hidden": []}
    saved = await h.call(
        "PUT", "/api/v1/me/preferences", json={"hidden": ["nav:crm", "home:quick", "nav:crm"]}
    )
    assert saved == {"hidden": ["home:quick", "nav:crm"]}
    assert (await h.call("GET", "/api/v1/me/preferences"))["hidden"] == ["home:quick", "nav:crm"]
    # Preferences are per person: the approver's are separate.
    assert (await h.call("GET", "/api/v1/me/preferences", as_approver=True)) == {"hidden": []}

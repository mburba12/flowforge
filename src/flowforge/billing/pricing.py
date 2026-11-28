"""Usage pricing: every price is the cost of what was used, marked up to the target margin.

    price = (usage cost + card fixed fee) / (1 - margin - card percent fee)

so after the card processor's fee the margin on every invoice is exactly the target
(70% by default). Rates are settings (FLOWFORGE_COST_*), see docs/KROV_PRICING.md.
"""

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from flowforge.core.config import settings

GB = Decimal(1_000_000_000)
CENT = Decimal("0.01")


def _d(value: float) -> Decimal:
    return Decimal(str(value))


@dataclass(frozen=True)
class Rates:
    cost_storage_gb_month: Decimal
    cost_per_1k_requests: Decimal
    cost_bank_connection_month: Decimal
    bill_bank_connections: bool
    margin: Decimal
    card_percent: Decimal
    card_fixed: Decimal
    currency: str

    @property
    def divisor(self) -> Decimal:
        return Decimal(1) - self.margin - self.card_percent

    def price_of(self, cost: Decimal) -> Decimal:
        """Customer price for a unit cost (no card fixed fee)."""
        return cost / self.divisor

    def public(self) -> dict[str, Any]:
        """Customer-facing unit prices."""
        return {
            "storage_gb_month": str(
                self.price_of(self.cost_storage_gb_month).quantize(Decimal("0.0001"))
            ),
            "per_1k_requests": str(
                self.price_of(self.cost_per_1k_requests).quantize(Decimal("0.0001"))
            ),
            "bank_connection_month": str(
                self.price_of(self.cost_bank_connection_month).quantize(Decimal("0.0001"))
            )
            if self.bill_bank_connections
            else "0",
            "payment_processing": str(self.price_of(self.card_fixed).quantize(CENT)),
            "currency": self.currency,
            "margin": str(self.margin),
        }


def current_rates() -> Rates:
    return Rates(
        cost_storage_gb_month=_d(settings.cost_storage_gb_month),
        cost_per_1k_requests=_d(settings.cost_per_1k_requests),
        cost_bank_connection_month=_d(settings.cost_bank_connection_month),
        bill_bank_connections=settings.bill_bank_connections,
        margin=_d(settings.target_margin),
        card_percent=_d(settings.card_fee_percent),
        card_fixed=_d(settings.card_fee_fixed),
        currency=settings.billing_currency,
    )


@dataclass(frozen=True)
class Usage:
    storage_gb_months: Decimal  # average stored GB over the month (GB-months)
    requests: int  # billable requests (imports and sync are free)
    bank_account_months: Decimal  # connected bank accounts averaged over the month


@dataclass(frozen=True)
class Line:
    code: str
    description: str
    quantity: str
    unit: str
    unit_price: str
    amount: str
    cost: str


def quote(usage: Usage, rates: Rates | None = None) -> dict[str, Any]:
    """The bill for a month's usage: lines, total, our cost and the resulting margin."""
    r = rates or current_rates()
    parts: list[tuple[str, str, Decimal, str, Decimal]] = [
        (
            "storage",
            "Storage (your records and files)",
            usage.storage_gb_months,
            "GB-month",
            r.cost_storage_gb_month,
        ),
        (
            "requests",
            "Activity (thousands of actions)",
            Decimal(usage.requests) / 1000,
            "1,000 actions",
            r.cost_per_1k_requests,
        ),
    ]
    if r.bill_bank_connections:
        parts.append(
            (
                "bank",
                "Live bank connections",
                usage.bank_account_months,
                "account-month",
                r.cost_bank_connection_month,
            )
        )
    lines: list[Line] = []
    cost = Decimal(0)
    for code, description, quantity, unit, unit_cost in parts:
        line_cost = quantity * unit_cost
        cost += line_cost
        amount = r.price_of(line_cost)
        lines.append(
            Line(
                code,
                description,
                str(quantity.quantize(Decimal("0.0001"))),
                unit,
                str(r.price_of(unit_cost).quantize(Decimal("0.0001"))),
                str(amount.quantize(CENT, ROUND_HALF_UP)),
                str(line_cost.quantize(Decimal("0.0001"))),
            )
        )
    processing = r.price_of(r.card_fixed)
    lines.append(
        Line(
            "processing",
            "Card payment processing",
            "1",
            "payment",
            str(processing.quantize(CENT)),
            str(processing.quantize(CENT, ROUND_HALF_UP)),
            str(r.card_fixed),
        )
    )
    total = sum((Decimal(line.amount) for line in lines), Decimal(0)).quantize(CENT, ROUND_HALF_UP)
    card_fee = (total * r.card_percent + r.card_fixed).quantize(Decimal("0.0001"))
    profit = total - cost - card_fee
    return {
        "lines": [asdict(line) for line in lines],
        "total": str(total),
        "currency": r.currency,
        "cost_basis": str(cost.quantize(Decimal("0.0001"))),
        "card_fee": str(card_fee),
        "profit": str(profit.quantize(CENT)),
        "margin": str((profit / total).quantize(Decimal("0.001")) if total else Decimal(0)),
    }


# ------------------------------------------------------------------ business days
def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    last = (date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)) - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def _observed(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def us_bank_holidays(year: int) -> set[date]:
    """US federal holidays as banks observe them (weekend dates move to Friday/Monday)."""
    return {
        _observed(date(year, 1, 1)),
        _nth_weekday(year, 1, 0, 3),  # Martin Luther King Jr. Day
        _nth_weekday(year, 2, 0, 3),  # Washington's Birthday
        _last_weekday(year, 5, 0),  # Memorial Day
        _observed(date(year, 6, 19)),  # Juneteenth
        _observed(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),  # Labor Day
        _nth_weekday(year, 10, 0, 2),  # Columbus Day
        _observed(date(year, 11, 11)),  # Veterans Day
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving
        _observed(date(year, 12, 25)),
    }


def add_business_days(start: date, days: int) -> date:
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in us_bank_holidays(current.year):
            added += 1
    return current

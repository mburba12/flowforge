from decimal import Decimal

from flowforge.phase4e.engine import (
    available_to_promise,
    commerce_to_cash,
    payroll_to_funding,
    three_way_match,
)


def test_commerce_balanced() -> None:
    assert all(
        row.within_tolerance
        for row in commerce_to_cash(
            Decimal(100),
            Decimal(100),
            Decimal("99.50"),
            Decimal("99.50"),
            Decimal("0.50"),
        )
    )


def test_procure_variance() -> None:
    assert (
        three_way_match(Decimal(10), Decimal(9), Decimal(9), Decimal(0))[0].within_tolerance
        is False
    )


def test_payroll() -> None:
    assert payroll_to_funding(Decimal(1000), Decimal(1000), Decimal(999), Decimal(1))[
        1
    ].within_tolerance


def test_atp() -> None:
    assert available_to_promise(Decimal(10), Decimal(3), Decimal(2)) == Decimal(9)

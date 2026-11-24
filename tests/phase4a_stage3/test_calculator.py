from decimal import Decimal

import pytest

from flowforge.phase4a_stage3.calculator import calculate_payroll


def test_hourly_gross_to_net() -> None:
    result = calculate_payroll(
        Decimal("40"),
        Decimal("5"),
        Decimal("20"),
        Decimal("100"),
        Decimal("50"),
        Decimal("25"),
        Decimal("0.20"),
        Decimal("0.08"),
    )
    assert result.gross_pay == Decimal("1050.00")
    assert result.taxable_wages == Decimal("1000.00")
    assert result.employee_taxes == Decimal("200.00")
    assert result.net_pay == Decimal("775.00")
    assert result.employer_taxes == Decimal("80.00")


def test_negative_net_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_payroll(
            Decimal("1"),
            Decimal("0"),
            Decimal("10"),
            Decimal("0"),
            Decimal("20"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        )

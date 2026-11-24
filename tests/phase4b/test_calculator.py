from decimal import Decimal

from flowforge.phase4b.calculator import calculate_tax


def test_employee_tax() -> None:
    r = calculate_tax(Decimal("1000"), Decimal("0.05"), "employee")
    assert r.employee_amount == Decimal("50.00")


def test_wage_base() -> None:
    r = calculate_tax(Decimal("1000"), Decimal("0.10"), "both", Decimal("500"))
    assert r.employer_amount == Decimal("50.00")

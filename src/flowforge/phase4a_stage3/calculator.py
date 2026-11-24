from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

MONEY = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class PayrollResult:
    gross_pay: Decimal
    pretax_deductions: Decimal
    taxable_wages: Decimal
    employee_taxes: Decimal
    posttax_deductions: Decimal
    net_pay: Decimal
    employer_taxes: Decimal


def calculate_payroll(
    regular_hours: Decimal,
    overtime_hours: Decimal,
    hourly_rate: Decimal,
    bonus: Decimal,
    pretax_deductions: Decimal,
    posttax_deductions: Decimal,
    employee_tax_rate: Decimal,
    employer_tax_rate: Decimal,
) -> PayrollResult:
    regular = regular_hours * hourly_rate
    overtime = overtime_hours * hourly_rate * Decimal("1.5")
    gross = regular + overtime + bonus
    taxable = max(gross - pretax_deductions, Decimal("0"))
    employee_tax = taxable * employee_tax_rate
    employer_tax = taxable * employer_tax_rate
    net = gross - pretax_deductions - employee_tax - posttax_deductions
    if net < 0:
        raise ValueError("Payroll deductions exceed gross pay")
    return PayrollResult(
        gross.quantize(MONEY, rounding=ROUND_HALF_UP),
        pretax_deductions.quantize(MONEY, rounding=ROUND_HALF_UP),
        taxable.quantize(MONEY, rounding=ROUND_HALF_UP),
        employee_tax.quantize(MONEY, rounding=ROUND_HALF_UP),
        posttax_deductions.quantize(MONEY, rounding=ROUND_HALF_UP),
        net.quantize(MONEY, rounding=ROUND_HALF_UP),
        employer_tax.quantize(MONEY, rounding=ROUND_HALF_UP),
    )

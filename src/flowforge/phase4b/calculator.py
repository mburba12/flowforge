from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

MONEY = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class TaxResult:
    taxable_wages: Decimal
    employee_amount: Decimal
    employer_amount: Decimal
    explanation: str


def calculate_tax(
    taxable_wages: Decimal,
    rate: Decimal,
    responsibility: str,
    wage_base: Decimal | None = None,
    additional_withholding: Decimal = Decimal("0"),
    exempt: bool = False,
) -> TaxResult:
    if exempt:
        return TaxResult(taxable_wages, Decimal("0"), Decimal("0"), "Worker election is exempt")
    base = taxable_wages if wage_base is None else min(taxable_wages, wage_base)
    amount = (base * rate).quantize(MONEY, rounding=ROUND_HALF_UP)
    employee = amount if responsibility in {"employee", "both"} else Decimal("0")
    employer = amount if responsibility in {"employer", "both"} else Decimal("0")
    employee += additional_withholding
    return TaxResult(
        base, employee, employer, f"base={base}; rate={rate}; responsibility={responsibility}"
    )

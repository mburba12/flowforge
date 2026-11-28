from decimal import ROUND_HALF_UP, Decimal


def straight_line(cost: Decimal, salvage: Decimal, periods: int) -> Decimal:
    if periods <= 0 or salvage > cost:
        raise ValueError("Invalid depreciation inputs")
    return ((cost - salvage) / periods).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def disposal_gain(proceeds: Decimal, book_value: Decimal) -> Decimal:
    return proceeds - book_value

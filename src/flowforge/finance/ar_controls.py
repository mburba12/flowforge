from decimal import Decimal


def allocate(balance: Decimal, receipt: Decimal) -> tuple[Decimal, Decimal]:
    if balance < 0 or receipt < 0:
        raise ValueError("Amounts must be nonnegative")
    applied = min(balance, receipt)
    return balance - applied, receipt - applied

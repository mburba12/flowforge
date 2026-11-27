from decimal import Decimal


def budget_variance(actual: Decimal, budget: Decimal) -> dict[str, Decimal]:
    return {"actual": actual, "budget": budget, "variance": actual - budget}


def assert_unlocked(locked: bool) -> None:
    if locked:
        raise PermissionError("Budget version is locked")

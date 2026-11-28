from decimal import Decimal

from flowforge.core.errors import RuleViolation


def budget_variance(actual: Decimal, budget: Decimal) -> dict[str, Decimal]:
    return {"actual": actual, "budget": budget, "variance": actual - budget}


def assert_unlocked(locked: bool) -> None:
    if locked:
        raise RuleViolation("Budget version is locked")

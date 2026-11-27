from decimal import Decimal


def reconcile(
    source: Decimal, target: Decimal, tolerance: Decimal = Decimal("0")
) -> dict[str, object]:
    variance = source - target
    return {
        "source": source,
        "target": target,
        "variance": variance,
        "reconciled": abs(variance) <= tolerance,
    }

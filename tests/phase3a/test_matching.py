from decimal import Decimal

from flowforge.phase3a.matching import MatchInput, MatchPolicy, evaluate


def test_match():
    assert (
        evaluate(
            MatchInput(Decimal("10"), Decimal("10"), Decimal("10"), Decimal("5"), Decimal("5")),
            MatchPolicy(),
        )[0]
        == "matched"
    )


def test_variance():
    assert (
        "price_variance"
        in evaluate(
            MatchInput(Decimal("10"), Decimal("10"), Decimal("10"), Decimal("5"), Decimal("7")),
            MatchPolicy(),
        )[1]
    )

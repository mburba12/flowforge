import pytest

from flowforge.phase4d.matching import score_match


@pytest.mark.parametrize(
    ("signals", "score", "decision"),
    [
        ({"tax_identifier_hash_exact": True}, 100, "proposal"),
        ({"provider_cross_reference_exact": True}, 100, "proposal"),
        ({"email_hash_exact": True}, 80, "manual_review"),
        ({"phone_hash_exact": True}, 70, "manual_review"),
        ({"legal_name_exact": True}, 50, "none"),
        ({"email_hash_exact": True, "website_domain_exact": True}, 100, "proposal"),
    ],
)
def test_scoring(signals: dict[str, bool], score: int, decision: str) -> None:
    result = score_match(signals)
    assert result.score == score
    assert result.decision == decision

from flowforge.phase2a.duplicates import DuplicateEvidence, score


def test_exact_identifier_blocks() -> None:
    s, r = score(DuplicateEvidence("acme", "acme", identifier_match=True))
    assert s == 100 and "identifier" in r


def test_possible_duplicate() -> None:
    s, _ = score(DuplicateEvidence("acme incorporated", "acme inc", country_match=True))
    assert 20 <= s <= 70

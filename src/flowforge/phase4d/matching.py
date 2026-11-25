from dataclasses import dataclass

WEIGHTS = {
    "tax_identifier_hash_exact": 100,
    "provider_cross_reference_exact": 100,
    "email_hash_exact": 80,
    "phone_hash_exact": 70,
    "legal_name_exact": 50,
    "website_domain_exact": 40,
    "address_fingerprint_exact": 40,
}


@dataclass(frozen=True, slots=True)
class MatchResult:
    score: int
    confidence_band: str
    decision: str
    signals: tuple[str, ...]


def score_match(signals: dict[str, bool]) -> MatchResult:
    matched = tuple(
        sorted(name for name, enabled in signals.items() if enabled and name in WEIGHTS)
    )
    score = min(100, sum(WEIGHTS[name] for name in matched))
    if score >= 90:
        return MatchResult(score, "high", "proposal", matched)
    if score >= 70:
        return MatchResult(score, "medium", "manual_review", matched)
    return MatchResult(score, "low", "none", matched)

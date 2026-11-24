from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True, slots=True)
class DuplicateEvidence:
    name_a: str
    name_b: str
    identifier_match: bool = False
    email_match: bool = False
    phone_match: bool = False
    address_similarity: float = 0
    postal_match: bool = False
    country_match: bool = False


def score(e: DuplicateEvidence) -> tuple[int, list[str]]:
    total = 0
    reasons = []
    if e.identifier_match:
        total += 100
        reasons.append("identifier")
    if e.email_match:
        total += 70
        reasons.append("email")
    if e.phone_match:
        total += 55
        reasons.append("phone")
    n = int(40 * SequenceMatcher(None, e.name_a, e.name_b).ratio())
    total += n
    if n >= 30:
        reasons.append("name")
    a = int(35 * max(0, min(1, e.address_similarity)))
    total += a
    if a >= 25:
        reasons.append("address")
    if e.postal_match:
        total += 15
        reasons.append("postal")
    if e.country_match:
        total += 10
        reasons.append("country")
    return min(total, 100), reasons

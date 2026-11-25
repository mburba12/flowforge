import hmac
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256


class Outcome(StrEnum):
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class ProviderResult:
    provider: str
    external_id: str | None
    outcome: Outcome
    raw_status: str


def normalize_result(provider: str, external_id: str | None, raw_status: str) -> ProviderResult:
    normalized = raw_status.casefold()
    if normalized in {"succeeded", "completed", "accepted", "posted", "confirmed"}:
        outcome = Outcome.CONFIRMED
    elif normalized in {"failed", "rejected", "declined", "cancelled"}:
        outcome = Outcome.REJECTED
    else:
        outcome = Outcome.UNCERTAIN
    return ProviderResult(provider, external_id, outcome, raw_status)


def verify_webhook(secret: bytes, body: bytes, signature: str) -> bool:
    expected = hmac.new(secret, body, sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def require_confirmed(result: ProviderResult) -> None:
    if result.outcome is not Outcome.CONFIRMED or not result.external_id:
        raise RuntimeError("Provider outcome is not confirmed")

import hashlib
import hmac

import pytest

from flowforge.phase5b.providers import Outcome, normalize_result, require_confirmed, verify_webhook


def test_normalize():
    assert normalize_result("stripe", "pi_1", "succeeded").outcome is Outcome.CONFIRMED


def test_uncertain():
    with pytest.raises(RuntimeError):
        require_confirmed(normalize_result("x", None, "timeout"))


def test_webhook():
    secret = b"s"
    body = b"{}"
    sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
    assert verify_webhook(secret, body, sig)

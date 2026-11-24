import hmac
from uuid import uuid4

from flowforge.phase1b.integrations import IntegrationService, SecretBox


def test_secret_cursor_webhook():
    b = SecretBox("a-long-development-key")
    s = IntegrationService(b)
    c = s.connect(uuid4(), "microsoft365", "secret")
    assert c.encrypted_secret != "secret" and b.decrypt(c.encrypted_secret) == "secret"
    s.update_cursor(c, "42")
    body = b"x"
    sig = hmac.new(b"secret", body, "sha256").hexdigest()
    assert s.verify_webhook(body, sig, "secret")

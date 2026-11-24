from uuid import uuid4

from flowforge.phase1a.security import Claims, TokenService, hash_password, verify_password


def test_security():
    h = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", h)
    c = Claims(uuid4(), uuid4(), uuid4(), "j1")
    assert TokenService().decode(TokenService().issue(c)).tenant_id == c.tenant_id

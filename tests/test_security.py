import jwt

from flowforge.core.config import settings
from flowforge.core.security import create_access_token, hash_password, verify_password


def test_password_hash() -> None:
    encoded = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", encoded)
    assert not verify_password("wrong-password", encoded)


def test_token() -> None:
    token = create_access_token(
        "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"
    )
    data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    assert data["tenant_id"].endswith("2")

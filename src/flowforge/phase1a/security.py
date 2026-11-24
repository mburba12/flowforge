from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from flowforge.core.config import settings

from .errors import AuthenticationError

_hash = PasswordHash.recommended()


def hash_password(value: str) -> str:
    return _hash.hash(value)


def verify_password(value: str, encoded: str) -> bool:
    return _hash.verify(value, encoded)


def opaque_token() -> str:
    return token_urlsafe(48)


def digest(value: str) -> str:
    return sha256(value.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Claims:
    user_id: UUID
    tenant_id: UUID
    session_id: UUID
    token_id: str


class TokenService:
    def issue(self, claims: Claims, minutes: int = 15) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(claims.user_id),
                "tenant_id": str(claims.tenant_id),
                "sid": str(claims.session_id),
                "jti": claims.token_id,
                "iat": now,
                "exp": now + timedelta(minutes=minutes),
            },
            settings.jwt_secret,
            algorithm="HS256",
        )

    def decode(self, token: str) -> Claims:
        try:
            x = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            return Claims(UUID(x["sub"]), UUID(x["tenant_id"]), UUID(x["sid"]), x["jti"])
        except (jwt.PyJWTError, KeyError, ValueError) as e:
            raise AuthenticationError("Invalid or expired token") from e

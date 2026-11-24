from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from flowforge.core.config import settings

password_hash = PasswordHash.recommended()
bearer = HTTPBearer()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(subject: str, tenant_id: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": subject,
            "tenant_id": tenant_id,
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


class Principal:
    def __init__(self, user_id: UUID, tenant_id: UUID):
        self.user_id = user_id
        self.tenant_id = tenant_id


def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> Principal:
    try:
        data = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        return Principal(UUID(data["sub"]), UUID(data["tenant_id"]))
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc

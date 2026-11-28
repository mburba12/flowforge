import asyncio
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

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


# Argon2 is deliberately slow and CPU-bound: run it in a worker thread so one sign-in
# never blocks every other request on the event loop.
async def hash_password_async(password: str) -> str:
    return await asyncio.to_thread(hash_password, password)


async def verify_password_async(password: str, encoded: str) -> bool:
    return await asyncio.to_thread(verify_password, password, encoded)


MFA_CHALLENGE_MINUTES = 5


def create_access_token(subject: str, tenant_id: str, mfa: bool = False) -> str:
    """A sign-in token: unique id (jti) so it can be revoked at sign-out, issue time so a
    password change ends it, and whether two-step sign-in was passed."""
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": subject,
            "tenant_id": tenant_id,
            "typ": "access",
            "jti": uuid4().hex,
            "mfa": mfa,
            "iat": now,
            "iat_ms": int(now.timestamp() * 1000),
            "exp": now + timedelta(minutes=settings.access_token_minutes),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def create_mfa_challenge(subject: str, tenant_id: str) -> str:
    """Proof that the password was right; good only for entering a code within 5 minutes."""
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": subject,
            "tenant_id": tenant_id,
            "typ": "mfa_challenge",
            "jti": uuid4().hex,
            "iat": now,
            "exp": now + timedelta(minutes=MFA_CHALLENGE_MINUTES),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def read_mfa_challenge(token: str) -> tuple[UUID, UUID, str]:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if data.get("typ") != "mfa_challenge":
            raise ValueError("not a challenge")
        return UUID(data["sub"]), UUID(data["tenant_id"]), str(data["jti"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "The sign-in expired. Please sign in again."
        ) from exc


class Principal:
    def __init__(
        self,
        user_id: UUID,
        tenant_id: UUID,
        jti: str | None = None,
        issued_at: datetime | None = None,
        mfa: bool = False,
        expires_at: datetime | None = None,
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.jti = jti
        self.issued_at = issued_at
        self.mfa = mfa
        self.expires_at = expires_at


def principal_from_token(token: str) -> Principal:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if data.get("typ", "access") != "access":
            raise ValueError("not a sign-in token")
        return Principal(
            UUID(data["sub"]),
            UUID(data["tenant_id"]),
            jti=data.get("jti"),
            issued_at=(
                datetime.fromtimestamp(int(data["iat_ms"]) / 1000, UTC)
                if "iat_ms" in data
                else datetime.fromtimestamp(int(data["iat"]), UTC)
                if "iat" in data
                else None
            ),
            mfa=bool(data.get("mfa", False)),
            expires_at=datetime.fromtimestamp(int(data["exp"]), UTC) if "exp" in data else None,
        )
    except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc


def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> Principal:
    return principal_from_token(credentials.credentials)

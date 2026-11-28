"""Account security tables (migration ff_security_002)."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from flowforge.core.encrypted_types import EncryptedText
from flowforge.db.base import Base


class UserMfa(Base):
    """A person's authenticator app: the secret (encrypted) and hashed recovery codes."""

    __tablename__ = "user_mfa"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    secret: Mapped[str] = mapped_column(EncryptedText("user_mfa.secret", 300))
    enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recovery_codes: Mapped[list[Any]] = mapped_column(JSON, default=list)
    last_step: Mapped[int] = mapped_column(BigInteger, default=0)


class AuthToken(Base):
    """A one-time link (password reset, email verification); only its hash is stored."""

    __tablename__ = "auth_tokens"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(20))
    subject_tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RevokedToken(Base):
    """A signed-out session (hash of the token id), kept until the token would expire."""

    __tablename__ = "revoked_tokens"
    jti_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

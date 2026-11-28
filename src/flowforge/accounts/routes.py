"""Endpoints: two-step sign-in, forgot/reset password, email verification, sign-out."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.config import settings
from flowforge.core.security import (
    Principal,
    create_access_token,
    current_principal,
    hash_password_async,
    read_mfa_challenge,
    verify_password_async,
)
from flowforge.db.session import enter_tenant_context, get_db, get_tenant_db
from flowforge.platform import ratelimit
from flowforge.platform.models import Tenant, User
from flowforge.platform.services import record_change

from . import totp
from .models import RevokedToken, UserMfa
from .policy import MFA_REQUIRED_FOR, owner_mfa_required, verified_email_required
from .service import (
    RESET_MINUTES,
    check_bot,
    send_link,
    send_notice,
    send_verification,
    take_link_token,
)

public = APIRouter(prefix="/api/v1/auth", tags=["auth"])
me = APIRouter(prefix="/api/v1/me", tags=["account security"])
signout = APIRouter(prefix="/api/v1/auth", tags=["auth"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]
Open = Annotated[AsyncSession, Depends(get_db)]

MFA_LIMIT = (10, 300)
FORGOT_LIMIT = (5, 900)


# ------------------------------------------------------------------ public
@public.get("/config")
async def auth_config() -> dict[str, Any]:
    """What the sign-in and sign-up pages need (the bot-check site key is public)."""
    return {"turnstile_site_key": settings.turnstile_site_key or None}


class MfaVerify(BaseModel):
    challenge: str = Field(min_length=20, max_length=2000)
    code: str = Field(min_length=6, max_length=20)


async def _mfa_row(db: AsyncSession, tenant_id: UUID, user_id: UUID) -> UserMfa | None:
    return await db.scalar(
        select(UserMfa).where(UserMfa.tenant_id == tenant_id, UserMfa.user_id == user_id)
    )


def _use_code(row: UserMfa, code: str) -> bool:
    """Accept an authenticator code (once) or an unused recovery code (removed)."""
    step = totp.verify(row.secret, code, row.last_step)
    if step is not None:
        row.last_step = step
        return True
    hashed = totp.hash_code(code)
    if hashed in (row.recovery_codes or []):
        row.recovery_codes = [c for c in row.recovery_codes if c != hashed]
        return True
    return False


@public.post("/mfa")
async def mfa_verify(body: MfaVerify, request: Request, db: Open) -> dict[str, str]:
    """Second step of signing in: the code from the authenticator app (or a recovery code)."""
    address = ratelimit.client_address(request)
    ratelimit.check(f"mfa:{address}", *MFA_LIMIT)
    user_id, tenant_id, jti = read_mfa_challenge(body.challenge)
    ratelimit.check(f"mfa-challenge:{jti}", 5, 300)
    await enter_tenant_context(db, tenant_id)
    row = await _mfa_row(db, tenant_id, user_id)
    user = await db.get(User, user_id)
    if row is None or row.enabled_at is None or user is None or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "The sign-in expired. Please sign in again."
        )
    if not _use_code(row, body.code):
        await db.commit()
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "That code is not right. Try the newest code."
        )
    await db.commit()
    return {
        "access_token": create_access_token(str(user_id), str(tenant_id), mfa=True),
        "token_type": "bearer",
    }


class Forgot(BaseModel):
    email: EmailStr
    turnstile_token: str | None = Field(default=None, max_length=4000)


@public.post("/password/forgot", status_code=202)
async def forgot_password(body: Forgot, request: Request, db: Open) -> dict[str, str]:
    """Email a reset link. The answer is the same whether or not the email has an account."""
    address = ratelimit.client_address(request)
    ratelimit.check(f"forgot:{address}", *FORGOT_LIMIT)
    await check_bot(body.turnstile_token, address)
    message = {"status": "If that email has an account, a reset link is on its way."}
    rows = await db.execute(text("SELECT ff_login_tenants(:e)"), {"e": body.email.lower()})
    for (tenant_id,) in rows.all():
        await enter_tenant_context(db, tenant_id)
        user = await db.scalar(
            select(User).where(User.tenant_id == tenant_id, User.email == body.email.lower())
        )
        if user is None or not user.is_active:
            continue
        from .service import issue_link_token

        token = await issue_link_token(db, user, "reset", timedelta(minutes=RESET_MINUTES))
        await db.commit()
        tenant = await db.get(Tenant, tenant_id)
        link = f"{settings.public_url.rstrip('/')}/reset-password#token={token}"
        await send_link(
            user.email,
            "Reset your Krov WorkAgent password",
            f"Reset your password for {tenant.name if tenant else 'Krov WorkAgent'}",
            f"Someone asked to reset your password. The link works for {RESET_MINUTES} minutes, once.",
            link,
            "Choose a new password",
        )
    return message


class Reset(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=12, max_length=200)


@public.post("/password/reset")
async def reset_password(body: Reset, request: Request, db: Open) -> dict[str, str]:
    ratelimit.check(f"reset:{ratelimit.client_address(request)}", 10, 900)
    row = await take_link_token(db, body.token, "reset")
    await enter_tenant_context(db, row.subject_tenant_id)
    user = await db.get(User, row.user_id)
    if user is None:
        raise HTTPException(400, "This link is no longer valid. Please ask for a new one.")
    user.password_hash = await hash_password_async(body.password)
    user.password_changed_at = datetime.now(UTC)  # every existing sign-in ends
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)  # the link proved the address
    await record_change(db, user.tenant_id, user.id, "password_reset", "user", str(user.id))
    await db.commit()
    await send_notice(
        user.email,
        "Your Krov WorkAgent password was changed",
        "Your password was just changed. If this was not you, reset it again now and tell your administrator.",
    )
    return {"status": "Password changed. Sign in with your new password."}


class Verify(BaseModel):
    token: str = Field(min_length=20, max_length=200)


@public.post("/email/verify")
async def verify_email(body: Verify, db: Open) -> dict[str, str]:
    row = await take_link_token(db, body.token, "verify")
    await enter_tenant_context(db, row.subject_tenant_id)
    user = await db.get(User, row.user_id)
    if user is None:
        raise HTTPException(400, "This link is no longer valid. Please ask for a new one.")
    user.email_verified_at = user.email_verified_at or datetime.now(UTC)
    await db.commit()
    return {"status": "Email confirmed."}


# ------------------------------------------------------------------ signed in
@signout.post("/logout")
async def logout(db: D, p: P) -> dict[str, str]:
    """End this sign-in on the server (the token stops working everywhere)."""
    if p.jti:
        expires = p.expires_at or datetime.now(UTC) + timedelta(
            minutes=settings.access_token_minutes
        )
        db.add(
            RevokedToken(jti_hash=hashlib.sha256(p.jti.encode()).hexdigest(), expires_at=expires)
        )
        await db.execute(delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(UTC)))
        await db.commit()
    return {"status": "signed out"}


@me.get("/security")
async def security_status(request: Request, db: D, p: P) -> dict[str, Any]:
    user = await db.get(User, p.user_id)
    row = await _mfa_row(db, p.tenant_id, p.user_id)
    granted: set[str] = set(getattr(request.state, "permissions", set()))
    return {
        "email": user.email if user else None,
        "email_verified": bool(user and user.email_verified_at),
        "email_verification_required": verified_email_required(),
        "mfa_enabled": bool(row and row.enabled_at),
        "mfa_required": owner_mfa_required() and bool(set(granted) & MFA_REQUIRED_FOR),
        "recovery_codes_left": len(row.recovery_codes or []) if row and row.enabled_at else 0,
    }


@me.post("/mfa/setup")
async def mfa_setup(db: D, p: P) -> dict[str, str]:
    """Start: a new secret for the authenticator app (not active until a code is confirmed)."""
    user = await db.get(User, p.user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    row = await _mfa_row(db, p.tenant_id, p.user_id)
    if row is not None and row.enabled_at is not None:
        raise HTTPException(
            409, "Two-step sign-in is already on. Turn it off first to change phones."
        )
    secret = totp.new_secret()
    if row is None:
        row = UserMfa(tenant_id=p.tenant_id, user_id=p.user_id, secret=secret, recovery_codes=[])
        db.add(row)
    else:
        row.secret = secret
    await db.commit()
    return {"secret": secret, "otpauth_uri": totp.otpauth_uri(secret, user.email)}


class Code(BaseModel):
    code: str = Field(min_length=6, max_length=20)


@me.post("/mfa/enable")
async def mfa_enable(body: Code, db: D, p: P) -> dict[str, Any]:
    row = await _mfa_row(db, p.tenant_id, p.user_id)
    if row is None or row.enabled_at is not None:
        raise HTTPException(409, "Start the setup first.")
    step = totp.verify(row.secret, body.code, row.last_step)
    if step is None:
        raise HTTPException(
            400, "That code is not right. Check the phone's clock and try the newest code."
        )
    codes = totp.new_recovery_codes()
    row.last_step = step
    row.enabled_at = datetime.now(UTC)
    row.recovery_codes = [totp.hash_code(c) for c in codes]
    await record_change(db, p.tenant_id, p.user_id, "mfa_enabled", "user", str(p.user_id))
    await db.commit()
    # A fresh sign-in that counts as two-step, so this session keeps working.
    return {
        "recovery_codes": codes,
        "access_token": create_access_token(str(p.user_id), str(p.tenant_id), mfa=True),
    }


@me.post("/mfa/disable")
async def mfa_disable(body: Code, request: Request, db: D, p: P) -> dict[str, str]:
    granted: set[str] = set(getattr(request.state, "permissions", set()))
    if owner_mfa_required() and set(granted) & MFA_REQUIRED_FOR:
        raise HTTPException(409, "Your role requires two-step sign-in, so it cannot be turned off.")
    row = await _mfa_row(db, p.tenant_id, p.user_id)
    if row is None or row.enabled_at is None:
        return {"status": "off"}
    if not _use_code(row, body.code):
        raise HTTPException(400, "That code is not right.")
    await db.delete(row)
    await record_change(db, p.tenant_id, p.user_id, "mfa_disabled", "user", str(p.user_id))
    await db.commit()
    return {"status": "off"}


@me.post("/email/resend")
async def resend_verification(request: Request, db: D, p: P) -> dict[str, str]:
    ratelimit.check(f"verify:{p.user_id}", 3, 3600)
    user = await db.get(User, p.user_id)
    if user is None or user.email_verified_at is not None:
        return {"status": "Already confirmed."}
    await send_verification(db, user)
    await db.commit()
    return {"status": f"We sent a new link to {user.email}."}


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=12, max_length=200)


@me.post("/password")
async def change_password(body: PasswordChange, db: D, p: P) -> dict[str, str]:
    user = await db.get(User, p.user_id)
    if user is None or not await verify_password_async(body.current_password, user.password_hash):
        raise HTTPException(400, "The current password is not right.")
    user.password_hash = await hash_password_async(body.new_password)
    user.password_changed_at = datetime.now(UTC)
    await record_change(db, p.tenant_id, p.user_id, "password_changed", "user", str(p.user_id))
    await db.commit()
    await send_notice(
        user.email,
        "Your Krov WorkAgent password was changed",
        "Your password was just changed. If this was not you, reset it now and tell your administrator.",
    )
    # Other sign-ins end; this one continues with a fresh token.
    return {"access_token": create_access_token(str(p.user_id), str(p.tenant_id), mfa=p.mfa)}

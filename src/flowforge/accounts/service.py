"""Shared account-security helpers: one-time links, emails, the bot check."""

import hashlib
import html
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.config import settings
from flowforge.platform.models import User

from .models import AuthToken
from .policy import verified_email_required

RESET_MINUTES = 30
VERIFY_DAYS = 7


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def issue_link_token(db: AsyncSession, user: User, purpose: str, lifetime: timedelta) -> str:
    token = secrets.token_urlsafe(32)
    db.add(
        AuthToken(
            token_hash=token_hash(token),
            purpose=purpose,
            subject_tenant_id=user.tenant_id,
            user_id=user.id,
            expires_at=datetime.now(UTC) + lifetime,
        )
    )
    await db.flush()
    return token


async def take_link_token(db: AsyncSession, token: str, purpose: str) -> AuthToken:
    """The unused, unexpired token for this link (marked used), or 400."""
    row = await db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == token_hash(token), AuthToken.purpose == purpose
        )
    )
    if row is None or row.used_at is not None or row.expires_at <= datetime.now(UTC):
        raise HTTPException(400, "This link is no longer valid. Please ask for a new one.")
    row.used_at = datetime.now(UTC)
    return row


def _page(title: str, body: str, link: str, button: str) -> str:
    return (
        f"<div style='font-family:Segoe UI,Arial,sans-serif;max-width:520px;color:#0f172a'>"
        f"<h2>Krov WorkAgent</h2><p><b>{html.escape(title)}</b></p><p>{html.escape(body)}</p>"
        f"<p><a href='{html.escape(link)}' style='background:#2563eb;color:#fff;padding:10px 16px;"
        f"border-radius:8px;text-decoration:none'>{html.escape(button)}</a></p>"
        f"<p style='color:#555;font-size:13px'>If you did not ask for this, ignore this email.</p></div>"
    )


async def send_link(to: str, subject: str, title: str, body: str, link: str, button: str) -> None:
    text = f"{title}\n\n{body}\n\n{link}\n\nIf you did not ask for this, ignore this email."
    from flowforge.billing import mailer  # imported here: billing imports this module

    try:
        await mailer.send([to], subject, text, _page(title, body, link, button))
    except mailer.MailNotSent:
        pass  # kept in the mail outbox; the person can ask again


async def send_verification(db: AsyncSession, user: User) -> None:
    token = await issue_link_token(db, user, "verify", timedelta(days=VERIFY_DAYS))
    link = f"{settings.public_url.rstrip('/')}/verify-email#token={token}"
    await send_link(
        user.email,
        "Confirm your email for Krov WorkAgent",
        "Confirm your email address",
        "Click the button to confirm this is your email. The link works for 7 days.",
        link,
        "Confirm my email",
    )


async def send_notice(to: str, subject: str, body: str) -> None:
    from flowforge.billing import mailer  # imported here: billing imports this module

    try:
        await mailer.send([to], subject, body, f"<p>{html.escape(body)}</p>")
    except mailer.MailNotSent:
        pass


async def require_verified_email(db: AsyncSession, user_id: UUID) -> None:
    if not verified_email_required():
        return
    verified = await db.scalar(select(User.email_verified_at).where(User.id == user_id))
    if verified is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Please confirm your email address first (we sent you a link; you can resend it from the banner).",
        )


async def check_bot(token: str | None, remote_ip: str) -> None:
    """Cloudflare Turnstile: required when FLOWFORGE_TURNSTILE_SECRET is set."""
    if not settings.turnstile_secret:
        return
    if not token:
        raise HTTPException(400, "Please complete the check that you are not a robot.")
    from flowforge.connect.http import client  # imported here: connect imports this module

    try:
        async with client() as http:
            response = await http.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": settings.turnstile_secret,
                    "response": token,
                    "remoteip": remote_ip,
                },
            )
        ok = bool(response.json().get("success"))
    except (httpx.HTTPError, ValueError):
        ok = False
    if not ok:
        raise HTTPException(400, "The robot check did not pass. Please try again.")

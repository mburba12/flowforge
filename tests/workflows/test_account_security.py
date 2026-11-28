"""Security: encryption at rest and key rotation, two-step sign-in, password reset,
email verification, sign-out, the bot check and closed bootstrap."""

import base64
import email
import email.policy
import os
import re
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from flowforge.accounts import totp
from flowforge.connect import http as provider_http
from flowforge.core import crypto
from flowforge.core.config import settings
from flowforge.db.session import engine
from flowforge.platform import ratelimit

from . import payroll_helpers as ph
from .conftest import Harness

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture
def outbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "mail_outbox", str(tmp_path / "mail"))
    monkeypatch.setattr(settings, "public_url", "https://app.example.test")
    ratelimit.reset()
    return tmp_path / "mail"


@pytest.fixture
def new_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    key = base64.b64encode(os.urandom(32)).decode()
    yield key
    crypto.reset_keys()


def _links(outbox: Path, kind: str) -> list[str]:
    """One-time link tokens in the plain-text part of every email in the outbox."""
    found: list[str] = []
    for mail in outbox.glob("*.eml"):
        message = email.message_from_bytes(mail.read_bytes(), policy=email.policy.default)
        body = message.get_body(("plain",))
        text = body.get_content() if body is not None else ""
        found += re.findall(rf"/{kind}#token=([A-Za-z0-9_\-]+)", text)
    return found


def test_values_and_files_are_sealed_and_keys_rotate(
    monkeypatch: pytest.MonkeyPatch, new_key: str
) -> None:
    # Start from the legacy setup (no dedicated key), whatever the environment has.
    monkeypatch.setattr(settings, "credentials_key", "")
    monkeypatch.setattr(settings, "credentials_key_previous", "")
    crypto.reset_keys()
    legacy_text = crypto.encrypt("acct-123456789", "ctx")  # sealed with the JWT-derived key
    legacy_file = crypto.encrypt_bytes(PDF, "file")
    assert crypto.decrypt(legacy_text, "ctx") == "acct-123456789"
    monkeypatch.setattr(settings, "credentials_key", new_key)
    crypto.reset_keys()
    # Old values stay readable, are flagged for re-encryption, and move to the new key.
    assert crypto.decrypt(legacy_text, "ctx") == "acct-123456789"
    assert crypto.needs_reencryption(legacy_text) and crypto.bytes_need_reencryption(legacy_file)
    fresh = crypto.encrypt("acct-123456789", "ctx")
    assert not crypto.needs_reencryption(fresh)
    assert crypto.decrypt_bytes(crypto.encrypt_bytes(PDF, "file"), "file") == PDF
    # The context is authenticated: a value moved to another column does not decrypt.
    with pytest.raises(Exception):  # noqa: B017
        crypto.decrypt(fresh, "other")
    # Plain values (stored before encryption) are always flagged.
    assert crypto.needs_reencryption("plain") and crypto.bytes_need_reencryption(PDF)


async def test_bank_numbers_and_files_are_encrypted_in_the_database(harness: Harness) -> None:
    h = harness
    worker_id = await ph.worker(h)
    await h.post(
        f"/api/v4a/workers/{worker_id}/bank-accounts",
        json={
            "account_token": "000123456789",
            "account_last4": "6789",
            "routing_token": "021000021",
            "account_type": "checking",
        },
    )
    raw = await h.sql(
        "SELECT account_token, routing_token FROM worker_bank_accounts WHERE worker_id = :w",
        w=worker_id,
    )
    assert raw and all(v.startswith("ffc2:") for v in raw[0])
    assert "000123456789" not in raw[0][0]

    files = {"file": ("invoice.pdf", PDF, "application/pdf")}
    up = await h.client.post("/api/v1/files", headers=h.owner, data={"section": "ap"}, files=files)
    assert up.status_code in (200, 201), up.text
    stored = await h.sql("SELECT id, content FROM attachments WHERE filename = 'invoice.pdf'")
    assert bytes(stored[0][1])[:4] == b"FFE2" and PDF not in bytes(stored[0][1])
    download = await h.client.get(f"/api/v1/files/{stored[0][0]}/content", headers=h.owner)
    assert download.content == PDF


async def _turn_on_mfa(h: Harness) -> tuple[str, list[str], dict[str, str]]:
    setup = await h.post("/api/v1/me/mfa/setup")
    secret = setup["secret"]
    assert setup["otpauth_uri"].startswith("otpauth://totp/")
    await h.post("/api/v1/me/mfa/enable", json={"code": "000000"}, expect=400)
    enabled = await h.post(
        "/api/v1/me/mfa/enable", json={"code": totp.code_at(secret, totp.current_step())}
    )
    return secret, enabled["recovery_codes"], {"Authorization": f"Bearer {enabled['access_token']}"}


async def test_two_step_sign_in(harness: Harness, outbox: Path) -> None:
    h = harness
    email = f"mfa-{uuid4().hex[:8]}@example.com"
    password = f"Mfa-{uuid4().hex}"
    await h.post(
        "/api/v1/users",
        json={"email": email, "display_name": "M", "password": password, "roles": ["Manager"]},
    )
    login = (
        await h.client.post("/api/v1/auth/login", json={"email": email, "password": password})
    ).json()
    old = {"Authorization": f"Bearer {login['access_token']}"}
    h.owner, keep = old, h.owner  # act as the new person
    try:
        secret, recovery, fresh = await _turn_on_mfa(h)
    finally:
        h.owner = keep
    # The sign-in from before two-step sign-in was turned on stops working.
    assert (await h.client.get("/api/v1/me/security", headers=old)).status_code == 401
    assert (await h.client.get("/api/v1/me/security", headers=fresh)).json()["mfa_enabled"] is True
    assert len(recovery) == 10

    # Signing in now needs the code: password alone gives only a challenge.
    first = (
        await h.client.post("/api/v1/auth/login", json={"email": email, "password": password})
    ).json()
    assert first["mfa_required"] is True and "access_token" not in first
    # The challenge is not a sign-in token.
    assert (
        await h.client.get("/api/v1/me", headers={"Authorization": f"Bearer {first['challenge']}"})
    ).status_code == 401
    bad = await h.client.post(
        "/api/v1/auth/mfa", json={"challenge": first["challenge"], "code": "123456"}
    )
    assert bad.status_code == 401
    step = totp.current_step() + 1  # a code the earlier setup did not use
    good = await h.client.post(
        "/api/v1/auth/mfa",
        json={"challenge": first["challenge"], "code": totp.code_at(secret, step)},
    )
    assert good.status_code == 200, good.text
    # The same code cannot be used twice.
    again = (
        await h.client.post("/api/v1/auth/login", json={"email": email, "password": password})
    ).json()
    reuse = await h.client.post(
        "/api/v1/auth/mfa",
        json={"challenge": again["challenge"], "code": totp.code_at(secret, step)},
    )
    assert reuse.status_code == 401
    # A recovery code works once.
    ok = await h.client.post(
        "/api/v1/auth/mfa", json={"challenge": again["challenge"], "code": recovery[0]}
    )
    assert ok.status_code == 200
    third = (
        await h.client.post("/api/v1/auth/login", json={"email": email, "password": password})
    ).json()
    once = await h.client.post(
        "/api/v1/auth/mfa", json={"challenge": third["challenge"], "code": recovery[0]}
    )
    assert once.status_code == 401


async def test_owners_must_set_up_two_step_sign_in(
    harness: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness
    monkeypatch.setattr(settings, "require_owner_mfa", "on")
    blocked = await h.client.get("/api/v1/users", headers=h.owner)
    assert blocked.status_code == 403
    assert blocked.json()["detail"]["code"] == "mfa_enrollment_required"
    status = await h.call("GET", "/api/v1/me/security")
    assert status["mfa_required"] is True and status["mfa_enabled"] is False
    _, _, fresh = await _turn_on_mfa(h)
    assert (await h.client.get("/api/v1/users", headers=fresh)).status_code == 200
    # Required for owners, so it cannot be switched off.
    off = await h.client.post("/api/v1/me/mfa/disable", headers=fresh, json={"code": "123456"})
    assert off.status_code == 409


async def test_sign_out_ends_the_session(harness: Harness) -> None:
    h = harness
    login = await h.client.post(
        "/api/v1/auth/login", json={"email": "x@example.com", "password": "nope"}
    )
    assert login.status_code == 401
    assert (await h.client.get("/api/v1/me", headers=h.approver)).status_code == 200
    assert (await h.client.post("/api/v1/auth/logout", headers=h.approver)).status_code == 200
    assert (await h.client.get("/api/v1/me", headers=h.approver)).status_code == 401


async def test_forgot_and_reset_password(harness: Harness, outbox: Path) -> None:
    h = harness
    email = f"reset-{uuid4().hex[:8]}@example.com"
    old_password = f"Old-{uuid4().hex}"
    await h.post(
        "/api/v1/users",
        json={"email": email, "display_name": "R", "password": old_password, "roles": ["Viewer"]},
    )
    signed_in = (
        await h.client.post("/api/v1/auth/login", json={"email": email, "password": old_password})
    ).json()
    session = {"Authorization": f"Bearer {signed_in['access_token']}"}

    same = await h.client.post(
        "/api/v1/auth/password/forgot", json={"email": "nobody-here@example.com"}
    )
    asked = await h.client.post("/api/v1/auth/password/forgot", json={"email": email})
    assert same.status_code == asked.status_code == 202 and same.json() == asked.json()
    tokens = _links(outbox, "reset-password")
    assert len(tokens) == 1

    new_password = f"New-{uuid4().hex}"
    await h.client.post(
        "/api/v1/auth/password/reset", json={"token": tokens[0], "password": "short"}
    )
    done = await h.client.post(
        "/api/v1/auth/password/reset", json={"token": tokens[0], "password": new_password}
    )
    assert done.status_code == 200, done.text
    # The link works once; the old password and the old session stop working.
    again = await h.client.post(
        "/api/v1/auth/password/reset", json={"token": tokens[0], "password": new_password}
    )
    assert again.status_code == 400
    assert (await h.client.get("/api/v1/me", headers=session)).status_code == 401
    assert (
        await h.client.post("/api/v1/auth/login", json={"email": email, "password": old_password})
    ).status_code == 401
    assert (
        await h.client.post("/api/v1/auth/login", json={"email": email, "password": new_password})
    ).status_code == 200
    # Only the hash of the link is stored.
    stored = await h.sql("SELECT count(*) FROM auth_tokens WHERE token_hash = :t", t=tokens[0])
    assert stored[0][0] == 0


async def test_sign_up_sends_verification_and_gates_money(
    harness: Harness, outbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness
    monkeypatch.setattr(settings, "require_verified_email", "on")
    tag = uuid4().hex[:8]
    made = await h.client.post(
        "/api/v1/auth/signup",
        json={
            "organization": f"Verify Co {tag}",
            "name": "V",
            "email": f"v-{tag}@example.com",
            "password": f"Verify-{uuid4().hex}",
        },
    )
    assert made.status_code == 201, made.text
    auth = {"Authorization": f"Bearer {made.json()['access_token']}"}
    slug = made.json()["tenant_slug"]
    try:
        assert (await h.client.get("/api/v1/me/security", headers=auth)).json()[
            "email_verified"
        ] is False
        blocked = await h.client.post(
            "/api/v1/users",
            headers=auth,
            json={
                "email": f"x-{tag}@example.com",
                "display_name": "X",
                "password": f"Xx-{uuid4().hex}",
                "roles": ["Viewer"],
            },
        )
        assert blocked.status_code == 403 and "confirm your email" in blocked.text
        tokens = _links(outbox, "verify-email")
        assert len(tokens) == 1
        assert (
            await h.client.post("/api/v1/auth/email/verify", json={"token": tokens[0]})
        ).status_code == 200
        assert (await h.client.get("/api/v1/me/security", headers=auth)).json()[
            "email_verified"
        ] is True
    finally:
        from sqlalchemy import text

        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM tenants WHERE slug = :s"), {"s": slug})
        await engine.dispose()


async def test_bot_check_and_closed_bootstrap(
    harness: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness
    monkeypatch.setattr(settings, "turnstile_secret", "secret-x")
    answers = {"good": True}
    provider_http.TRANSPORT = httpx.MockTransport(
        lambda r: httpx.Response(200, json={"success": answers["good"]})
    )
    try:
        body = {
            "organization": "Bot Co",
            "name": "B",
            "email": f"b-{uuid4().hex[:6]}@example.com",
            "password": f"Bot-{uuid4().hex}",
        }
        assert (await h.client.post("/api/v1/auth/signup", json=body)).status_code == 400
        answers["good"] = False
        assert (
            await h.client.post("/api/v1/auth/signup", json={**body, "turnstile_token": "t"})
        ).status_code == 400
    finally:
        provider_http.TRANSPORT = None
    monkeypatch.setattr(settings, "allow_bootstrap", "off")
    closed = await h.client.post(
        "/api/v1/auth/bootstrap",
        json={
            "tenant": {"name": "Closed Co", "slug": "closed-co"},
            "email": "a@example.com",
            "password": "a" * 12,
            "display_name": "A",
        },
    )
    assert closed.status_code == 404


async def test_security_headers(harness: Harness) -> None:
    response = await harness.client.get("/api/v1/me", headers=harness.owner)
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"

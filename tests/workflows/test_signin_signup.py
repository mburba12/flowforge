"""Sign in with email only, public sign-up, and the public endpoint limits."""

from collections.abc import Iterator
from uuid import uuid4

import pytest
from sqlalchemy import text

from flowforge.core.config import settings
from flowforge.db.session import engine
from flowforge.platform import ratelimit

from .conftest import Harness


@pytest.fixture
def limits_on() -> Iterator[None]:
    previous = settings.rate_limits
    settings.rate_limits = "on"
    ratelimit.reset()
    yield
    settings.rate_limits = previous
    ratelimit.reset()


async def _drop_tenants(*slugs: str) -> None:
    async with engine.begin() as conn:
        for slug in slugs:
            await conn.execute(text("DELETE FROM tenants WHERE slug = :s"), {"s": slug})
    await engine.dispose()


async def test_sign_in_with_email_only(harness: Harness) -> None:
    h = harness
    me = await h.call("GET", "/api/v1/me")
    users = await h.call("GET", "/api/v1/users")
    owner_email = next(u["email"] for u in users if str(u["email"]).startswith("owner-"))
    # The harness owner password is not exposed; the approver signs in the same way.
    approver_email = next(u["email"] for u in users if str(u["email"]).startswith("approver-"))
    assert owner_email and approver_email

    password = f"Pw-{uuid4().hex}"
    email = f"solo-{uuid4().hex[:8]}@example.com"
    made = await h.post(
        "/api/v1/users",
        json={"email": email, "display_name": "Solo", "password": password, "roles": ["Viewer"]},
    )
    assert made["email"] == email

    ok = await h.client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert ok.status_code == 200, ok.text
    token = ok.json()["access_token"]
    who = await h.client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert who.json()["tenant_id"] == me["tenant_id"]

    wrong = await h.client.post(
        "/api/v1/auth/login", json={"email": email, "password": "nope-nope"}
    )
    assert wrong.status_code == 401
    unknown = await h.client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": password}
    )
    assert unknown.status_code == 401
    assert unknown.json() == wrong.json()  # nothing tells whether the email exists


async def test_public_sign_up_creates_a_workspace_and_signs_in(harness: Harness) -> None:
    h = harness
    tag = uuid4().hex[:8]
    email = f"founder-{tag}@example.com"
    password = f"Founder-{uuid4().hex}"
    slugs: list[str] = []
    try:
        made = await h.client.post(
            "/api/v1/auth/signup",
            json={
                "organization": f"Acme Plumbing {tag}",
                "name": "Pat Founder",
                "email": email,
                "password": password,
                "plan": "business",
            },
        )
        assert made.status_code == 201, made.text
        body = made.json()
        slugs.append(body["tenant_slug"])
        assert body["tenant_slug"] == f"acme-plumbing-{tag}"
        auth = {"Authorization": f"Bearer {body['access_token']}"}
        perms = (await h.client.get("/api/v1/me/permissions", headers=auth)).json()
        assert "users.manage" in perms["permissions"]  # the founder is the Owner

        again = await h.client.post(
            "/api/v1/auth/signup",
            json={"organization": "Other", "name": "Pat", "email": email, "password": password},
        )
        assert again.status_code == 409
        assert "Sign in instead" in again.text

        # Same organization name, different person: a distinct workspace address.
        other = await h.client.post(
            "/api/v1/auth/signup",
            json={
                "organization": f"Acme Plumbing {tag}",
                "name": "Sam",
                "email": f"sam-{tag}@example.com",
                "password": password,
            },
        )
        assert other.status_code == 201, other.text
        slugs.append(other.json()["tenant_slug"])
        assert other.json()["tenant_slug"].startswith(f"acme-plumbing-{tag}-")

        signed_in = await h.client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert signed_in.status_code == 200

        short = await h.client.post(
            "/api/v1/auth/signup",
            json={
                "organization": "X Co",
                "name": "P",
                "email": f"x-{tag}@example.com",
                "password": "short",
            },
        )
        assert short.status_code == 422
    finally:
        await _drop_tenants(*slugs)


async def test_email_in_two_workspaces_asks_which_one(harness: Harness) -> None:
    h = harness
    tag = uuid4().hex[:8]
    email = f"both-{tag}@example.com"
    password = f"Both-{uuid4().hex}"
    first = await h.client.post(
        "/api/v1/auth/signup",
        json={"organization": f"First {tag}", "name": "B", "email": email, "password": password},
    )
    assert first.status_code == 201, first.text
    slug = first.json()["tenant_slug"]
    try:
        # The same person is also a user in the harness workspace.
        await h.post(
            "/api/v1/users",
            json={"email": email, "display_name": "B", "password": password, "roles": ["Viewer"]},
        )
        choose = await h.client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert choose.status_code == 409
        detail = choose.json()["detail"]
        assert detail["code"] == "workspace_required"
        assert slug in {w["slug"] for w in detail["workspaces"]}
        picked = await h.client.post(
            "/api/v1/auth/login", json={"email": email, "password": password, "tenant_slug": slug}
        )
        assert picked.status_code == 200
    finally:
        await _drop_tenants(slug)


async def test_public_endpoints_are_rate_limited(harness: Harness, limits_on: None) -> None:
    h = harness
    statuses = [
        (
            await h.client.post(
                "/api/v1/auth/login",
                json={"email": "guess@example.com", "password": f"wrong-{n}"},
                headers={"CF-Connecting-IP": "203.0.113.7"},
            )
        ).status_code
        for n in range(12)
    ]
    assert statuses[:10] == [401] * 10
    assert statuses[10:] == [429, 429]
    # Another address is not affected.
    other = await h.client.post(
        "/api/v1/auth/login",
        json={"email": "guess@example.com", "password": "wrong"},
        headers={"CF-Connecting-IP": "203.0.113.8"},
    )
    assert other.status_code == 401

    signups = []
    for n in range(6):
        response = await h.client.post(
            "/api/v1/auth/signup",
            json={"organization": "", "name": "x", "email": f"rl{n}@example.com", "password": "x"},
            headers={"CF-Connecting-IP": "203.0.113.9"},
        )
        signups.append(response.status_code)
    # Invalid bodies are refused before counting (422); the limit applies to real attempts.
    assert set(signups) == {422}

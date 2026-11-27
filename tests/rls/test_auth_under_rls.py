"""Bootstrap and login must work as the restricted runtime role under forced RLS.

Regression for: bootstrap returned HTTP 500 ("new row violates row-level
security policy for table roles") and login could not see users, because
neither flow installed app.current_tenant_id before touching tenant-owned
tables. They only worked when the API connected as a role bypassing RLS.

Runs only against a database where the connection is a non-superuser without
BYPASSRLS and users has forced RLS; otherwise it is skipped (it would prove
nothing against a superuser connection).
"""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text

from flowforge.db.session import engine
from flowforge.main import app


async def _restricted_rls_connection() -> str | None:
    """Return None when the environment qualifies, else the skip reason."""
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT r.rolsuper, r.rolbypassrls,"
                        " coalesce((SELECT relforcerowsecurity FROM pg_class"
                        "  WHERE oid = to_regclass('public.users')), false)"
                        " FROM pg_roles r WHERE r.rolname = current_user"
                    )
                )
            ).one()
    except Exception as exc:  # noqa: BLE001 - any connection problem means skip
        return f"database unavailable: {type(exc).__name__}"
    superuser, bypass, forced = row
    if superuser or bypass:
        return "connected role bypasses RLS"
    if not forced:
        return "public.users does not have forced RLS"
    return None


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    reason = await _restricted_rls_connection()
    if reason:
        await engine.dispose()
        pytest.skip(reason)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://rls-test") as c:
        yield c
    await engine.dispose()


async def _delete_tenant(tenant_id: UUID) -> None:
    # tenants has no RLS; ON DELETE CASCADE foreign keys remove owned rows.
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tenant_id})


async def test_bootstrap_and_login_under_rls(client: httpx.AsyncClient) -> None:
    slug = f"rls-test-{uuid4().hex[:12]}"
    email = f"{slug}@example.com"
    password = f"Rls-{uuid4().hex}"
    tenant_id: UUID | None = None
    try:
        created = await client.post(
            "/api/v1/auth/bootstrap",
            json={
                "tenant": {"name": "RLS Test", "slug": slug},
                "email": email,
                "password": password,
                "display_name": "RLS Owner",
            },
        )
        assert created.status_code == 201, created.text

        token = created.json()["access_token"]
        me = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200, me.text
        tenant_id = UUID(str(me.json()["tenant_id"]))

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password, "tenant_slug": slug},
        )
        assert login.status_code == 200, login.text
        assert login.json()["access_token"]

        wrong = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "not-the-password", "tenant_slug": slug},
        )
        assert wrong.status_code == 401

        duplicate = await client.post(
            "/api/v1/auth/bootstrap",
            json={
                "tenant": {"name": "RLS Test", "slug": slug},
                "email": email,
                "password": password,
                "display_name": "RLS Owner",
            },
        )
        assert duplicate.status_code == 409
    finally:
        if tenant_id is None:
            async with engine.connect() as conn:
                found = await conn.scalar(
                    text("SELECT id FROM tenants WHERE slug = :s"), {"s": slug}
                )
            tenant_id = found
        if tenant_id is not None:
            await _delete_tenant(tenant_id)

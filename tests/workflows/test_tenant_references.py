"""Records can only reference records of their own tenant (migration ff_security_001)."""

from uuid import uuid4

from sqlalchemy import text

from flowforge.db.session import engine

from .conftest import IN_PERIOD, Harness


async def test_every_tenant_reference_is_checked() -> None:
    """Every single-column FK from a tenant table to another tenant table's id is covered."""
    async with engine.connect() as conn:
        expected = {
            (row[0], row[1])
            for row in await conn.execute(
                text(
                    "SELECT c.conrelid::regclass::text, a.attname FROM pg_constraint c"
                    " JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]"
                    " JOIN pg_attribute ra"
                    " ON ra.attrelid = c.confrelid AND ra.attnum = c.confkey[1]"
                    " WHERE c.contype = 'f' AND array_length(c.conkey, 1) = 1"
                    " AND c.connamespace = 'public'::regnamespace AND ra.attname = 'id'"
                    " AND c.confrelid::regclass::text <> 'tenants'"
                    " AND EXISTS (SELECT 1 FROM pg_attribute x WHERE x.attrelid = c.conrelid"
                    "   AND x.attname = 'tenant_id' AND NOT x.attisdropped)"
                    " AND EXISTS (SELECT 1 FROM pg_attribute x WHERE x.attrelid = c.confrelid"
                    "   AND x.attname = 'tenant_id' AND NOT x.attisdropped)"
                )
            )
        }
        covered: set[tuple[str, str]] = set()
        for table, args in await conn.execute(
            text(
                "SELECT tgrelid::regclass::text, encode(tgargs, 'escape') FROM pg_trigger"
                " WHERE tgname = 'ff_same_tenant' AND NOT tgisinternal"
            )
        ):
            values = args.split("\\000")
            covered.update((table, values[i]) for i in range(0, len(values) - 1, 2))
    await engine.dispose()
    missing = sorted(expected - covered)
    assert not missing, (
        f"run SELECT ff_install_same_tenant_triggers() in a migration: {missing[:10]}"
    )


async def test_another_tenant_cannot_reference_our_records(harness: Harness) -> None:
    h = harness
    ours = await h.organization("Our Customer")
    slug = f"other-{uuid4().hex[:8]}"
    created = await h.client.post(
        "/api/v1/auth/bootstrap",
        json={
            "tenant": {"name": "Other tenant", "slug": slug},
            "email": f"owner-{slug}@example.com",
            "password": f"Other-{uuid4().hex}",
            "display_name": "Other Owner",
        },
    )
    other = {"Authorization": f"Bearer {created.json()['access_token']}"}
    other_tenant = (await h.client.get("/api/v1/me", headers=other)).json()["tenant_id"]
    try:
        quote = {
            "quote_number": f"Q-{uuid4().hex[:6]}",
            "party_id": ours,
            "currency_code": "USD",
            "lines": [{"description": "Item", "quantity": "1", "unit_price": "5.00"}],
        }
        stolen = await h.client.post("/api/v2/crm/quotes", headers=other, json=quote)
        assert stolen.status_code == 409, stolen.text
        assert "tenant" not in stolen.text.lower() or "conflict" in stolen.text.lower()
        timecard = await h.client.post(
            "/api/v2/workforce/ultimate/clock-events",
            headers=other,
            json={
                "worker_id": ours,
                "event_type": "clock_in",
                "occurred_at": f"{IN_PERIOD}T09:00:00Z",
            },
        )
        assert timecard.status_code in (409, 422), timecard.text
        # The same request referencing the other tenant's own party succeeds.
        party = await h.client.post(
            "/api/v2/organizations",
            headers=other,
            json={"legal_name": "Their Customer"},
        )
        assert party.status_code == 201, party.text
        own = await h.client.post(
            "/api/v2/crm/quotes", headers=other, json={**quote, "party_id": party.json()["id"]}
        )
        assert own.status_code == 201, own.text
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM tenants WHERE id = :i"), {"i": other_tenant})
        await engine.dispose()

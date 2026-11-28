"""Shared harness for release-scope live workflow tests (AP, AR, Payroll, Tax).

Each test runs the real FastAPI app in-process (httpx ASGI transport) against
the real database, connected as the restricted runtime role under forced RLS.
Tests are skipped, with the reason, unless that environment is present (for
example when the suite runs against a superuser database).

Every test gets its own tenant, owner and second approver, general ledger
(currency, calendar, open period, ledger, chart of accounts). The tenant is
deleted at the end; ON DELETE CASCADE removes all owned rows.

All setup goes through the public API (users, periods, authorities included).
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text

from flowforge.db.session import engine
from flowforge.main import app

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 1, 31)
IN_PERIOD = date(2026, 1, 15)

ACCOUNTS: dict[str, tuple[str, str, str]] = {
    # key: (code, type, normal balance)
    "cash": ("1000", "asset", "debit"),
    "ar": ("1100", "asset", "debit"),
    "inventory": ("1200", "asset", "debit"),
    "ap": ("2000", "liability", "credit"),
    "employee_tax_payable": ("2100", "liability", "credit"),
    "employer_tax_payable": ("2110", "liability", "credit"),
    "deductions_payable": ("2120", "liability", "credit"),
    "net_pay_payable": ("2130", "liability", "credit"),
    "tax_payable": ("2200", "liability", "credit"),
    "equity": ("3000", "equity", "credit"),
    "revenue": ("4000", "revenue", "credit"),
    "cogs": ("5000", "expense", "debit"),
    "expense": ("6000", "expense", "debit"),
    "wages": ("6100", "expense", "debit"),
    "employer_tax_expense": ("6110", "expense", "debit"),
}


async def _skip_reason() -> str | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT r.rolsuper, r.rolbypassrls,"
                        " coalesce((SELECT relforcerowsecurity FROM pg_class"
                        "  WHERE oid = to_regclass('public.journal_entries')), false)"
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
        return "journal_entries does not have forced RLS"
    return None


@dataclass
class Harness:
    client: httpx.AsyncClient
    tenant_id: UUID
    owner: dict[str, str]
    approver: dict[str, str]
    ledger_id: str = ""
    period_id: str = ""
    calendar_id: str = ""
    accounts: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------ HTTP
    async def call(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        as_approver: bool = False,
        expect: int | tuple[int, ...] = (200, 201),
    ) -> Any:
        headers = self.approver if as_approver else self.owner
        response = await self.client.request(
            method, path, json=json, params=params, headers=headers
        )
        allowed = (expect,) if isinstance(expect, int) else expect
        assert response.status_code in allowed, (
            f"{method} {path} -> {response.status_code} (expected {allowed}): {response.text}"
        )
        return response.json() if response.content else None

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.call("POST", path, **kwargs)

    # ------------------------------------------------------------------ SQL
    async def sql(self, statement: str, **params: Any) -> list[Any]:
        """Run SQL as the restricted role inside this tenant's RLS context."""
        async with engine.begin() as conn:
            await conn.execute(
                text("SELECT set_config('app.current_tenant_id', :t, true)"),
                {"t": str(self.tenant_id)},
            )
            result = await conn.execute(text(statement), params)
            return list(result.all()) if result.returns_rows else []

    async def unbalanced_journals(self) -> list[Any]:
        return await self.sql(
            "SELECT j.journal_number, sum(l.debit) d, sum(l.credit) c"
            " FROM journal_entries j JOIN journal_lines l ON l.journal_id = j.id"
            " GROUP BY j.id, j.journal_number HAVING sum(l.debit) <> sum(l.credit)"
        )

    async def posted_totals(self) -> tuple[Decimal, Decimal]:
        rows = await self.sql(
            "SELECT coalesce(sum(l.debit),0), coalesce(sum(l.credit),0)"
            " FROM journal_entries j JOIN journal_lines l ON l.journal_id = j.id"
            " WHERE j.status = 'posted' AND j.ledger_id = :l AND j.period_id = :p",
            l=self.ledger_id,
            p=self.period_id,
        )
        return Decimal(rows[0][0]), Decimal(rows[0][1])

    async def trial_balance(self) -> tuple[Decimal, Decimal]:
        tb = await self.call(
            "GET",
            "/api/v2/trial-balance",
            params={"ledger_id": self.ledger_id, "period_id": self.period_id},
        )
        return Decimal(tb["debit"]), Decimal(tb["credit"])

    async def account_balance(self, key: str) -> Decimal:
        """Net balance (debit - credit) of an account from the GL balance table."""
        rows = await self.sql(
            "SELECT coalesce(sum(debit_total - credit_total), 0) FROM account_balances"
            " WHERE account_id = :a AND ledger_id = :l AND period_id = :p",
            a=self.accounts[key],
            l=self.ledger_id,
            p=self.period_id,
        )
        return Decimal(rows[0][0])

    async def audit_count(self) -> int:
        rows = await self.sql("SELECT count(*) FROM audit_entries")
        return int(rows[0][0])

    async def assert_ledger_integrity(self) -> None:
        """Invariants every posting workflow must keep."""
        assert await self.unbalanced_journals() == [], "an unbalanced journal exists"
        posted_debit, posted_credit = await self.posted_totals()
        assert posted_debit == posted_credit, "posted journals do not balance in total"
        tb_debit, tb_credit = await self.trial_balance()
        assert (tb_debit, tb_credit) == (posted_debit, posted_credit), (
            "trial balance does not include all posted journals: "
            f"trial balance {tb_debit}/{tb_credit} vs posted journal lines "
            f"{posted_debit}/{posted_credit}"
        )

    # ------------------------------------------------------------------ setup
    async def setup_ledger(self) -> None:
        await self.post("/api/v2/currencies", json={"code": "USD", "name": "US Dollar"})
        cal = await self.post("/api/v2/fiscal-calendars", json={"name": "FY2026", "start_month": 1})
        self.calendar_id = cal["id"]
        period = await self.post(
            "/api/v2/accounting-periods",
            json={
                "calendar_id": self.calendar_id,
                "period_code": "2026-01",
                "start_date": PERIOD_START.isoformat(),
                "end_date": PERIOD_END.isoformat(),
            },
        )
        self.period_id = period["id"]
        ledger = await self.post(
            "/api/v2/ledgers", json={"code": "GL", "name": "General Ledger", "base_currency": "USD"}
        )
        self.ledger_id = ledger["id"]
        for key, (code, kind, normal) in ACCOUNTS.items():
            account = await self.post(
                "/api/v2/accounts",
                json={
                    "ledger_id": self.ledger_id,
                    "account_code": code,
                    "name": key.replace("_", " ").title(),
                    "account_type": kind,
                    "normal_balance": normal,
                    "posting_allowed": True,
                },
            )
            self.accounts[key] = account["id"]

    async def organization(self, name: str) -> str:
        party = await self.post("/api/v2/organizations", json={"legal_name": name})
        return str(party["id"])

    async def person(self, given: str, family: str) -> str:
        party = await self.post("/api/v2/people", json={"given_name": given, "family_name": family})
        return str(party["id"])

    async def require_two_people(self) -> None:
        """Take "approve own work" away from this tenant's Owner role.

        Owners may approve their own work (approvals.self_approve); flows that prove the
        two-person rule with the owner as creator call this first.
        """
        await self.sql(
            "DELETE FROM role_permissions rp USING roles r, permissions p"
            " WHERE rp.role_id = r.id AND rp.permission_id = p.id AND r.name = 'Owner'"
            " AND p.code = 'approvals.self_approve' AND r.tenant_id = :t",
            t=self.tenant_id,
        )

    async def close_period(self) -> None:
        await self.post(f"/api/v2/accounting-periods/{self.period_id}/close")

    async def tax_authority(self, jurisdiction_id: str, code: str) -> str:
        authority = await self.post(
            "/api/v4b/authorities",
            json={"jurisdiction_id": jurisdiction_id, "code": code, "name": f"{code} Authority"},
        )
        return str(authority["id"])


@pytest.fixture
async def harness() -> AsyncIterator[Harness]:
    reason = await _skip_reason()
    if reason:
        await engine.dispose()
        pytest.skip(reason)

    slug = f"wf-{uuid4().hex[:12]}"
    password = f"Wf-{uuid4().hex}"
    transport = httpx.ASGITransport(app=app)
    tenant_id: UUID | None = None
    async with httpx.AsyncClient(transport=transport, base_url="http://workflow-test") as client:
        try:
            created = await client.post(
                "/api/v1/auth/bootstrap",
                json={
                    "tenant": {"name": "Workflow Test", "slug": slug},
                    "email": f"owner-{slug}@example.com",
                    "password": password,
                    "display_name": "Workflow Owner",
                },
            )
            assert created.status_code == 201, created.text
            owner = {"Authorization": f"Bearer {created.json()['access_token']}"}
            me = (await client.get("/api/v1/me", headers=owner)).json()
            tenant_id = UUID(str(me["tenant_id"]))

            # Second user (approver/poster) created through the user-management API.
            approver_email = f"approver-{slug}@example.com"
            made = await client.post(
                "/api/v1/users",
                headers=owner,
                json={
                    "email": approver_email,
                    "display_name": "Workflow Approver",
                    "password": password,
                    "roles": ["Manager"],
                },
            )
            assert made.status_code == 201, made.text
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": approver_email, "password": password, "tenant_slug": slug},
            )
            assert login.status_code == 200, login.text
            approver = {"Authorization": f"Bearer {login.json()['access_token']}"}

            h = Harness(client=client, tenant_id=tenant_id, owner=owner, approver=approver)
            await h.setup_ledger()
            yield h
        finally:
            if tenant_id is None:
                async with engine.connect() as conn:
                    tenant_id = await conn.scalar(
                        text("SELECT id FROM tenants WHERE slug = :s"), {"s": slug}
                    )
            if tenant_id is not None:
                async with engine.begin() as conn:
                    await conn.execute(text("DELETE FROM tenants WHERE id = :i"), {"i": tenant_id})
            await engine.dispose()

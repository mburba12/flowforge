# ruff: noqa: E501 - audit tool: long SQL and request lines read better unwrapped
"""Functional audit: does every operation succeed when given valid input?

Runs the app in-process against the isolated database as the restricted role, on a
fresh tenant. Several passes call every operation with schema-generated input; ids
in paths and bodies are taken from records that exist (matched by the path segment
or field name). An operation is "working" once it has answered 2xx. The report lists
operations that never succeeded, with their last answer, for triage.

Usage: python tests/extended/functional_audit.py  (FLOWFORGE_DATABASE_URL must point
at the isolated test database). Report: var/functional-audit.json
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.responses import JSONResponse  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from flowforge.db.session import engine  # noqa: E402
from flowforge.main import app  # noqa: E402


async def _integrity_detail(_: Any, exc: IntegrityError) -> JSONResponse:
    # Audit only (in-process): expose the violated constraint for triage.
    return JSONResponse(
        status_code=409, content={"detail": "INTEGRITY " + str(exc.orig).splitlines()[-1][:300]}
    )


app.add_exception_handler(IntegrityError, _integrity_detail)  # type: ignore[arg-type]

REPORT = ROOT / "var" / "functional-audit.json"
PASSES = 16
DECISION_FIELDS = {"target", "stage", "status", "action", "decision", "to_status"}
SECOND_ACTOR = re.compile(
    r"creator|own |cannot approve|independent|another user|different user|segregation", re.I
)


KNOWN: dict[str, Any] = {}  # field name -> value, filled from the live API before the passes
FK: dict[str, list[str]] = {}  # column name -> referenced tables (from the database)


class Builder:
    def __init__(self, spec: dict[str, Any], ids: dict[str, list[str]], n: int, path: str = ""):
        self.components = spec.get("components", {}).get("schemas", {})
        self.ids = ids
        self.n = n
        self.path = path
        self.used: set[str] = set()

    def known(self, name: str) -> Any:
        segment = next(
            (
                s
                for s in ("commerce", "logistics", "finance", "workforce", "engagement", "payments")
                if f"/v4c/{s}/" in self.path
            ),
            "",
        )
        if name == "provider" and segment:
            return KNOWN.get(f"provider:{segment}")
        if name in ("permissions", "permission_codes"):
            return KNOWN.get("permissions")
        if name in ("public_token", "authorization_code"):
            return "sandbox-audit-token"
        if name in ("base_uom", "uom", "uom_code", "unit_of_measure"):
            return "CS"
        if name == "responsibility":
            return "employee"
        if name.endswith("_at") or name in ("occurred", "timestamp"):
            return datetime.now(UTC).isoformat()
        if name == "environment":
            return "sandbox"
        if "consent" in name or name in (
            "signature_valid",
            "accepted",
            "is_active",
            "active",
            "posting_allowed",
        ):
            return True
        if name in ("currency_code", "base_currency", "currency", "transaction_currency"):
            return "USD"
        if name == "code" and "/currencies" in self.path:
            return "USD"
        return None

    def resolve(self, schema: dict[str, Any]) -> dict[str, Any]:
        while "$ref" in schema:
            schema = self.components[schema["$ref"].split("/")[-1]]
        return schema

    def _pick(self, values: list[str]) -> str:
        for v in values:
            if v not in self.used:
                self.used.add(v)
                return v
        return values[0]

    def _table_for(self, stem: str) -> str | None:
        singular = stem.removesuffix("s")
        words = set(re.split(r"[/_{}-]+", self.path))
        scored = []
        for table in self.ids:
            norm = table.removesuffix("_final")
            if norm in (stem, singular) or norm.endswith(("_" + stem, "_" + singular, stem + "s")):
                shared = len(words & set(table.split("_")))
                scored.append((-shared, len(table), table))
        return min(scored)[2] if scored else None

    def id_for(self, name: str, hint: str = "") -> str:
        """An existing id: by the URL segment for path ids, else by foreign key or name."""
        if hint:
            table = self._table_for(hint.replace("-", "_"))
            if table:
                return self._pick(self.ids[table])
        targets = [x for x in FK.get(name, []) if self.ids.get(x)]
        if targets:
            words = set(re.split(r"[/_{}-]+", self.path))
            best = max(targets, key=lambda x: (len(words & set(x.split("_"))), -targets.index(x)))
            return self._pick(self.ids[best])
        if name not in {"id", "record_id"}:
            table = self._table_for(name.removesuffix("_ids").removesuffix("_id"))
            if table:
                return self._pick(self.ids[table])
        return str(uuid4())

    def value(self, schema: dict[str, Any], name: str = "", depth: int = 0, hint: str = "") -> Any:
        schema = self.resolve(schema)
        if depth > 6:
            return None
        for key in ("anyOf", "oneOf"):
            if key in schema:
                options = [
                    self.resolve(s) for s in schema[key] if self.resolve(s).get("type") != "null"
                ]
                return self.value(options[0], name, depth + 1, hint) if options else None
        if "allOf" in schema:
            return self.value(schema["allOf"][0], name, depth + 1, hint)
        hint_value = self.known(name)
        if hint_value is not None:
            return hint_value
        if "enum" in schema:
            options = schema["enum"]
            return options[self.n % len(options)] if name in DECISION_FIELDS else options[0]
        if "const" in schema:
            return schema["const"]
        pattern = schema.get("pattern", "")
        m = re.fullmatch(r"\^\(([\w|-]+)\)\$", pattern)
        if m:
            options = m.group(1).split("|")
            return options[self.n % len(options)] if name in DECISION_FIELDS else options[0]
        if "default" in schema and schema["default"] is not None:
            return schema["default"]
        kind = schema.get("type")
        fmt = schema.get("format", "")
        if kind == "object" or "properties" in schema:
            required = set(schema.get("required", []))
            props = schema.get("properties", {})
            out = {}
            for k, v in props.items():
                nullable = any(self.resolve(s).get("type") == "null" for s in v.get("anyOf", []))
                if k not in required and nullable:
                    continue  # optional: leave empty, as a user would
                out[k] = self.value(v, k, depth + 1)
            return out
        if kind == "array":
            count = max(int(schema.get("minItems", 1)), 1)
            items = []
            for i in range(count):
                item = self.value(schema.get("items", {}), name, depth + 1)
                if isinstance(item, str) and i > 0 and item in items:
                    pool = [v for vals in self.ids.values() for v in vals if v not in items]
                    item = pool[0] if pool else f"{item}-{i}"
                if item is not None:
                    items.append(item)
            return items
        if kind == "integer":
            lo = int(
                schema.get(
                    "minimum",
                    schema.get("exclusiveMinimum", 0) + 1 if "exclusiveMinimum" in schema else 1,
                )
            )
            hi = schema.get("maximum")
            v = max(lo, 1)
            if re.search(r"year", name):
                v = date.today().year
            if re.search(r"month", name):
                v = 1
            return min(v, int(hi)) if hi is not None else v
        if kind == "number":
            return max(float(schema.get("minimum", 1)), 1.0)
        if kind == "boolean":
            return False
        if fmt == "uuid" or name.endswith("_id") or name == "id":
            return self.id_for(name, hint)
        if fmt == "time" or name.endswith("_time"):
            return "17:00:00" if re.search(r"end|to|out", name) else "09:00:00"
        if fmt == "date":
            if name in ("pay_date", "payment_date", "check_date"):
                return (date.today() + timedelta(days=45)).isoformat()
            if re.search(r"end|to|until|due|expir", name):
                return (date.today() + timedelta(days=30)).isoformat()
            return date.today().isoformat()
        if fmt == "date-time":
            if re.search(r"end|to|until|due|expir", name):
                return (datetime.now(UTC) + timedelta(days=1)).isoformat()
            return datetime.now(UTC).isoformat()
        if fmt == "email" or name.endswith("email"):
            return f"audit-{uuid4().hex[:8]}@example.com"
        if fmt == "decimal" or re.search(
            r"amount|price|rate|qty|quantity|total|cost|hours|percent", name
        ):
            return "10.00"
        if re.search(r"currency", name):
            return "USD"
        if re.search(r"country", name):
            return "US"
        if re.search(r"(^|_)(url|uri)$|endpoint", name):
            return "https://example.com/hook"
        if name in DECISION_FIELDS:
            states = [
                "submitted",
                "approved",
                "active",
                "released",
                "posted",
                "completed",
                "closed",
                "won",
                "paid",
            ]
            return states[self.n % len(states)]
        min_len = max(int(schema.get("minLength", 1)), 1)
        max_len = int(schema.get("maxLength", 40))
        base = f"A{self.n}{uuid4().hex[:6]}-{name or 'v'}"
        sample = base if len(base) >= min_len else base + "x" * (min_len - len(base))
        return sample[:max_len] if max_len >= min_len else sample[:min_len]


def operations(spec: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    ops = []
    for path, item in spec["paths"].items():
        if path.startswith(("/openapi", "/docs", "/redoc")) or path.endswith("/auth/bootstrap"):
            continue
        for method, op in item.items():
            if method in {"get", "post", "put", "patch", "delete"}:
                ops.append((method.upper(), path, op))
    # Creates first (shorter paths are usually parents), then actions, reads, deletes.
    rank = {"POST": 0, "PUT": 1, "PATCH": 1, "GET": 2, "DELETE": 3}
    return sorted(ops, key=lambda o: (rank[o[0]], o[1].count("{"), o[1]))


async def load_foreign_keys() -> None:
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                # pg_catalog: information_schema hides constraints of tables the role does not own.
                "SELECT a.attname, ref.relname, count(*) FROM pg_constraint c"
                " JOIN pg_class ref ON ref.oid = c.confrelid"
                " JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]"
                " WHERE c.contype = 'f' AND array_length(c.conkey, 1) = 1"
                " GROUP BY 1, 2 ORDER BY 1, 3 DESC"
            )
        )
        for column, table, _ in rows:
            FK.setdefault(column, []).append(table)


async def collect_ids(tenant_id: str) -> dict[str, list[str]]:
    ids: dict[str, list[str]] = {}
    async with engine.begin() as conn:
        await conn.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id}
        )
        tables = await conn.execute(
            text(
                "SELECT c.table_name FROM information_schema.columns c"
                " JOIN information_schema.columns i ON i.table_name = c.table_name"
                "  AND i.table_schema = 'public' AND i.column_name = 'id' AND i.data_type = 'uuid'"
                " WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id'"
            )
        )
        for (table,) in tables:
            rows = await conn.execute(text(f'SELECT id FROM "{table}" ORDER BY ctid DESC LIMIT 3'))
            found = [str(r[0]) for r in rows]
            if found:
                ids[table] = found
    return ids


def path_hint(path: str, param: str) -> str:
    parts = [p for p in path.split("/") if p]
    token = "{" + param + "}"
    if token in parts:
        i = parts.index(token)
        if i > 0 and not parts[i - 1].startswith("{"):
            return parts[i - 1]
    return ""


async def main() -> None:
    spec = app.openapi()
    slug = f"audit-{uuid4().hex[:10]}"
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    results: dict[str, dict[str, Any]] = {}
    tenant_id = ""
    async with httpx.AsyncClient(transport=transport, base_url="http://audit") as client:
        try:
            created = await client.post(
                "/api/v1/auth/bootstrap",
                json={
                    "tenant": {"name": "Functional audit", "slug": slug},
                    "email": f"owner-{slug}@example.com",
                    "password": f"Audit-{uuid4().hex}",
                    "display_name": "Audit Owner",
                },
            )
            created.raise_for_status()
            headers = {"Authorization": f"Bearer {created.json()['access_token']}"}
            tenant_id = str((await client.get("/api/v1/me", headers=headers)).json()["tenant_id"])
            ops = operations(spec)
            second_email, second_password = f"manager-{slug}@example.com", f"Audit-{uuid4().hex}"
            await client.post(
                "/api/v1/users",
                headers=headers,
                json={
                    "email": second_email,
                    "display_name": "Audit Manager",
                    "password": second_password,
                    "roles": ["Manager"],
                },
            )
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": second_email, "password": second_password, "tenant_slug": slug},
            )
            manager = {"Authorization": f"Bearer {login.json()['access_token']}"}
            await load_foreign_keys()
            print("foreign-key columns mapped:", len(FK))
            for seg in ("commerce", "logistics", "finance", "workforce", "engagement"):
                r = await client.get(f"/api/v4c/{seg}/providers", headers=headers)
                if r.status_code == 200:
                    body = r.json()
                    items = (
                        body
                        if isinstance(body, list)
                        else body.get("items", body.get("providers", []))
                    )
                    if items:
                        first = items[0]
                        KNOWN[f"provider:{seg}"] = (
                            first if isinstance(first, str) else first.get("code")
                        )
            KNOWN["provider:payments"] = "stripe"
            perms = (await client.get("/api/v1/permissions", headers=headers)).json()
            KNOWN["permissions"] = [p["code"] if isinstance(p, dict) else p for p in perms][:3]
            for n in range(PASSES):
                ids = await collect_ids(tenant_id)
                for method, path, op in ops:
                    key = f"{method} {path}"
                    if results.get(key, {}).get("ok"):
                        continue
                    if method == "DELETE" and n < PASSES - 1:
                        continue
                    if path.endswith(("/users/{user_id}",)) and method == "PATCH":
                        continue  # would deactivate the audit owner
                    builder = Builder(spec, ids, n, path)
                    url, params = path, {}
                    for p in op.get("parameters", []):
                        v = builder.value(
                            p.get("schema", {}), p["name"], hint=path_hint(path, p["name"])
                        )
                        if p["in"] == "path":
                            url = url.replace("{" + p["name"] + "}", str(v))
                        elif p["in"] == "query" and (p.get("required") or n % 2):
                            params[p["name"]] = v
                    body = None
                    content = op.get("requestBody", {}).get("content", {})
                    if "application/json" in content:
                        body = builder.value(content["application/json"]["schema"], "body")
                    try:
                        r = await client.request(
                            method, url, params=params, json=body, headers=headers
                        )
                        status, detail = r.status_code, r.text[:400]
                        if status in (403, 409) and SECOND_ACTOR.search(detail):
                            r = await client.request(
                                method, url, params=params, json=body, headers=manager
                            )
                            status, detail = r.status_code, r.text[:400]
                    except Exception as exc:  # noqa: BLE001
                        status, detail = 599, f"{type(exc).__name__}: {exc}"[:400]
                    entry = results.setdefault(key, {"tags": op.get("tags", []), "ok": False})
                    entry.update(
                        last_status=status,
                        last_detail=detail,
                        last_body=body if status >= 400 else None,
                    )
                    if status < 300:
                        entry["ok"] = True
        finally:
            if tenant_id:
                async with engine.begin() as conn:
                    await conn.execute(
                        text("DELETE FROM tenants WHERE id = :i"), {"i": UUID(tenant_id)}
                    )
            await engine.dispose()
    failing = {k: v for k, v in results.items() if not v["ok"]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {
                "operations": len(results),
                "working": len(results) - len(failing),
                "never_succeeded": len(failing),
                "failing": dict(sorted(failing.items())),
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(
        f"operations={len(results)} working={len(results) - len(failing)} never_succeeded={len(failing)}"
    )


if __name__ == "__main__":
    asyncio.run(main())

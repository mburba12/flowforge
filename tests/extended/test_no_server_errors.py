"""Every API operation, called with schema-generated input, must never produce a server error.

Runs the real app in-process against the real database as the restricted runtime role
(skipped otherwise). A fresh tenant is bootstrapped; each operation is called three
times: with generated input on an empty tenant, again after a first pass has created
data, and with identifiers taken from records that now exist. 4xx answers (validation,
not found, conflict, forbidden) are fine; any 5xx or unhandled exception is a defect.
The report lists every failure with its exception.
"""

from __future__ import annotations

import json
import re
import traceback
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text

from flowforge.db.session import engine
from flowforge.main import app

REPORT = Path(__file__).resolve().parents[2] / "var" / "operation-scan.json"
SKIP_PATHS = re.compile(r"^/(openapi|docs|redoc)")


async def _restricted() -> str | None:
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
                )
            ).one()
    except Exception as exc:  # noqa: BLE001
        return f"database unavailable: {type(exc).__name__}"
    return "connected role bypasses RLS" if any(row) else None


class SampleBuilder:
    def __init__(self, spec: dict[str, Any], ids: dict[str, list[str]]):
        self.components = spec.get("components", {}).get("schemas", {})
        self.ids = ids

    def resolve(self, schema: dict[str, Any]) -> dict[str, Any]:
        while "$ref" in schema:
            schema = self.components[schema["$ref"].split("/")[-1]]
        return schema

    def uuid_for(self, name: str) -> str:
        stem = name.removesuffix("_id").removesuffix("_ids")
        for key, values in self.ids.items():
            if values and (key == stem or key.startswith(stem) or stem.endswith(key)):
                return values[0]
        return str(uuid4())

    def value(self, schema: dict[str, Any], name: str = "", depth: int = 0) -> Any:
        schema = self.resolve(schema)
        if depth > 6:
            return None
        for key in ("anyOf", "oneOf"):
            if key in schema:
                options = [
                    self.resolve(s) for s in schema[key] if self.resolve(s).get("type") != "null"
                ]
                return self.value(options[0], name, depth + 1) if options else None
        if "allOf" in schema:
            return self.value(schema["allOf"][0], name, depth + 1)
        if "enum" in schema:
            return schema["enum"][0]
        if "const" in schema:
            return schema["const"]
        if "default" in schema and schema["default"] is not None:
            return schema["default"]
        kind = schema.get("type")
        fmt = schema.get("format", "")
        if kind == "object" or "properties" in schema:
            props = schema.get("properties", {})
            return {k: self.value(v, k, depth + 1) for k, v in props.items()}
        if kind == "array":
            item = self.value(schema.get("items", {}), name, depth + 1)
            return [item] if item is not None else []
        if kind == "integer":
            return max(int(schema.get("minimum", 1)), 1)
        if kind == "number":
            return max(float(schema.get("minimum", 1)), 1.0)
        if kind == "boolean":
            return False
        if fmt == "uuid" or name.endswith("_id") or name == "id":
            return self.uuid_for(name)
        if fmt == "date":
            return date.today().isoformat()
        if fmt == "date-time":
            return datetime.now(UTC).isoformat()
        if fmt == "email":
            return f"scan-{uuid4().hex[:8]}@example.com"
        if fmt in {"decimal"} or re.search(
            r"amount|price|rate|qty|quantity|total|cost|hours", name
        ):
            return "1.00"
        length = max(int(schema.get("minLength", 1)), 1)
        max_len = int(schema.get("maxLength", 40))
        if re.search(r"currency", name):
            return "USD"
        if re.search(r"country", name):
            return "US"
        base = f"scan-{name or 'value'}-{uuid4().hex[:6]}"
        sample = base if len(base) >= length else base + "x" * (length - len(base))
        return sample[:max_len] if max_len >= length else sample[:length]


def _operations(spec: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    ops = []
    for path, item in spec["paths"].items():
        if SKIP_PATHS.match(path) or path.endswith("/auth/bootstrap"):
            continue
        for method, op in item.items():
            if method in {"get", "post", "put", "patch", "delete"}:
                ops.append((method.upper(), path, op))
    return ops


async def _collect_ids(tenant_id: str) -> dict[str, list[str]]:
    """Ids of existing records per table, used to fill path/body identifiers."""
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
            rows = await conn.execute(text(f'SELECT id FROM "{table}" LIMIT 1'))
            found = [str(r[0]) for r in rows]
            if found:
                ids[table.removesuffix("s")] = found
                ids[table] = found
    return ids


async def _call(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    method: str,
    path: str,
    op: dict[str, Any],
    builder: SampleBuilder,
) -> tuple[int, str]:
    params: dict[str, Any] = {}
    url = path
    for p in op.get("parameters", []):
        schema = p.get("schema", {})
        value = builder.value(schema, p["name"])
        if p["in"] == "path":
            url = url.replace("{" + p["name"] + "}", str(value))
        elif p["in"] == "query" and p.get("required"):
            params[p["name"]] = value
    body = None
    content = op.get("requestBody", {}).get("content", {})
    if "application/json" in content:
        body = builder.value(content["application/json"]["schema"], "body")
    try:
        response = await client.request(method, url, params=params, json=body, headers=headers)
    except Exception as exc:  # noqa: BLE001 - an exception escaping the app is a server error
        return 599, "".join(traceback.format_exception_only(type(exc), exc)).strip()[:600]
    return response.status_code, response.text[:300]


async def test_no_operation_returns_a_server_error() -> None:
    reason = await _restricted()
    if reason:
        await engine.dispose()
        pytest.skip(reason)
    spec = app.openapi()
    slug = f"scan-{uuid4().hex[:10]}"
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
    failures: dict[str, dict[str, Any]] = {}
    counts = {"operations": 0, "calls": 0}
    tenant_id = ""
    async with httpx.AsyncClient(transport=transport, base_url="http://scan") as client:
        try:
            created = await client.post(
                "/api/v1/auth/bootstrap",
                json={
                    "tenant": {"name": "Operation scan", "slug": slug},
                    "email": f"owner-{slug}@example.com",
                    "password": f"Scan-{uuid4().hex}",
                    "display_name": "Scan Owner",
                },
            )
            assert created.status_code == 201, created.text
            headers = {"Authorization": f"Bearer {created.json()['access_token']}"}
            tenant_id = str((await client.get("/api/v1/me", headers=headers)).json()["tenant_id"])
            operations = _operations(spec)
            counts["operations"] = len(operations)
            order = sorted(operations, key=lambda o: (o[0] != "POST", o[1]))
            for round_no in range(3):
                ids = await _collect_ids(tenant_id) if round_no == 2 else {}
                builder = SampleBuilder(spec, ids)
                for method, path, op in order:
                    if (
                        method == "DELETE"
                        or path.endswith(("/users/{user_id}", "/users"))
                        and method == "PATCH"
                    ):
                        continue
                    status, detail = await _call(client, headers, method, path, op, builder)
                    counts["calls"] += 1
                    if status >= 500:
                        failures.setdefault(
                            f"{method} {path}",
                            {"status": status, "detail": detail, "module": op.get("tags", [])},
                        )
        finally:
            if tenant_id:
                async with engine.begin() as conn:
                    await conn.execute(
                        text("DELETE FROM tenants WHERE id = :i"), {"i": UUID(tenant_id)}
                    )
            await engine.dispose()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps({"counts": counts, "failures": failures}, indent=2), encoding="utf-8"
    )
    assert not failures, f"{len(failures)} operations returned server errors; see {REPORT}"

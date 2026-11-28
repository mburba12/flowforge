# ruff: noqa: E501 - audit tool
"""Isolation and role audit over every operation.

1. The functional audit populates tenant A (every operation, real records).
2. Tenant B (a fresh tenant, its owner) calls every operation using A's real record ids
   in paths and bodies. A 2xx answer that references A's data, or any list response that
   contains one of A's ids, is a cross-tenant leak.
3. A Viewer in tenant A calls every mutating operation: anything but 401/403/404/405/422
   for a non-public, permission-mapped operation is a role leak.

Usage: python tests/extended/isolation_audit.py   Report: var/isolation-audit.json
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent))

import functional_audit as fa  # noqa: E402

from flowforge.platform.authorization import (  # noqa: E402
    EXTENDED_POLICY,
    POLICY,
    PUBLIC,
    endpoint_key,
    iter_routes_with_paths,
)

REPORT = fa.ROOT / "var" / "isolation-audit.json"
findings: dict[str, list[dict[str, Any]]] = {"cross_tenant": [], "role": []}
stats: dict[str, int] = {"cross_tenant_calls": 0, "role_calls": 0}


def permission_map(app: Any) -> dict[tuple[str, str], str | None]:
    out: dict[tuple[str, str], str | None] = {}
    for route, path in iter_routes_with_paths(list(app.routes)):
        key = endpoint_key(route.endpoint)
        perm = None if key in PUBLIC else POLICY.get(key, EXTENDED_POLICY.get(key))
        for method in route.methods or ():
            out[(method, path)] = perm
    return out


async def attack(
    client: Any, tenant_a: str, slug_a: str, headers_a: dict[str, str], spec: dict[str, Any]
) -> None:
    ids_a = await fa.collect_ids(tenant_a)
    all_a = {v for values in ids_a.values() for v in values}
    perms = permission_map(fa.app)

    # --- tenant B uses tenant A's ids everywhere
    slug_b = f"intruder-{uuid4().hex[:8]}"
    created = await client.post(
        "/api/v1/auth/bootstrap",
        json={
            "tenant": {"name": "Intruder tenant", "slug": slug_b},
            "email": f"owner-{slug_b}@example.com",
            "password": f"Audit-{uuid4().hex}",
            "display_name": "Intruder Owner",
        },
    )
    headers_b = {"Authorization": f"Bearer {created.json()['access_token']}"}
    tenant_b = str((await client.get("/api/v1/me", headers=headers_b)).json()["tenant_id"])
    try:
        for method, path, op in fa.operations(spec):
            if method == "DELETE" or (method == "PATCH" and path.endswith("/users/{user_id}")):
                continue
            builder = fa.Builder(spec, ids_a, 99, path)
            url, params = path, {}
            for p in op.get("parameters", []):
                v = builder.value(
                    p.get("schema", {}), p["name"], hint=fa.path_hint(path, p["name"])
                )
                if p["in"] == "path":
                    url = url.replace("{" + p["name"] + "}", str(v))
                elif p["in"] == "query" and p.get("required"):
                    params[p["name"]] = v
            content = op.get("requestBody", {}).get("content", {})
            body = (
                builder.value(content["application/json"]["schema"], "body")
                if "application/json" in content
                else None
            )
            r = await client.request(method, url, params=params, json=body, headers=headers_b)
            stats["cross_tenant_calls"] += 1
            if r.status_code >= 300:
                continue
            leaked = sorted(i for i in all_a if i in r.text)
            # A path id from tenant A that was accepted (2xx) is a leak unless the answer
            # is a fresh record of B's own (ids in the answer belong to B only).
            used_path_ids = [seg for seg in url.split("/") if seg in all_a]
            if leaked or used_path_ids:
                findings["cross_tenant"].append(
                    {
                        "operation": f"{method} {path}",
                        "status": r.status_code,
                        "leaked_ids": leaked[:5],
                        "path_ids": used_path_ids,
                        "response": r.text[:300],
                    }
                )
    finally:
        async with fa.engine.begin() as conn:
            await conn.execute(text("DELETE FROM tenants WHERE id = :i"), {"i": UUID(tenant_b)})

    # --- a Viewer in tenant A on every mutating operation
    email, password = f"viewer-{slug_a}@example.com", f"Audit-{uuid4().hex}"
    await client.post(
        "/api/v1/users",
        headers=headers_a,
        json={
            "email": email,
            "display_name": "Audit Viewer",
            "password": password,
            "roles": ["Viewer"],
        },
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password, "tenant_slug": slug_a}
    )
    viewer = {"Authorization": f"Bearer {login.json()['access_token']}"}
    for method, path, op in fa.operations(spec):
        if method == "GET":
            continue
        perm = perms.get((method, path))
        if perm is None or perm == "" or perm.endswith(".read"):
            continue  # public, any signed-in user, or a read-level action
        builder = fa.Builder(spec, ids_a, 98, path)
        url = path
        for p in op.get("parameters", []):
            if p["in"] == "path":
                url = url.replace(
                    "{" + p["name"] + "}",
                    str(
                        builder.value(
                            p.get("schema", {}), p["name"], hint=fa.path_hint(path, p["name"])
                        )
                    ),
                )
        content = op.get("requestBody", {}).get("content", {})
        body = (
            builder.value(content["application/json"]["schema"], "body")
            if "application/json" in content
            else None
        )
        r = await client.request(method, url, json=body, headers=viewer)
        stats["role_calls"] += 1
        if r.status_code != 403:
            findings["role"].append(
                {
                    "operation": f"{method} {path}",
                    "permission": perm,
                    "status": r.status_code,
                    "response": r.text[:200],
                }
            )


async def run() -> None:
    await fa.main(after_populate=attack)
    REPORT.write_text(
        json.dumps({"stats": stats, "findings": findings}, indent=2), encoding="utf-8"
    )
    print(
        f"isolation calls={stats['cross_tenant_calls']} leaks={len(findings['cross_tenant'])}; role calls={stats['role_calls']} leaks={len(findings['role'])}"
    )


if __name__ == "__main__":
    asyncio.run(run())

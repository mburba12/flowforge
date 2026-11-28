"""Import the approved data from the recovered database into the production database.

Approved scope (owner decision, 2026-11-27):
  * the current production tenant, its users (password hashes copied verbatim, so
    existing sign-in keeps working until the owner rotates the password), its roles,
    role permissions and user-role assignments, and the permission catalog
  * reference data: 57 US jurisdictions (tax.jurisdictions) and 9 payroll import
    providers (payroll.providers), owned by the production tenant
Not imported (archived in the recovered database): the 16 automated test-run
organizations, their business rows, the empty legacy production organization and
the 19 legacy identity users.

Idempotent: rows are keyed by their source IDs and inserted with ON CONFLICT DO
NOTHING; a rerun inserts nothing. The source session is read-only. Prints one JSON
reconciliation report; never prints secrets or password hashes.

Environment: IMPORT_SOURCE_DSN, IMPORT_TARGET_DSN (asyncpg/libpq DSNs, owner roles),
IMPORT_TENANT_SLUG (default flowforge-production).
"""

import asyncio
import json
import os
import sys

import asyncpg

TENANT_SLUG = os.environ.get("IMPORT_TENANT_SLUG", "flowforge-production")


async def main() -> int:
    src = await asyncpg.connect(os.environ["IMPORT_SOURCE_DSN"])
    dst = await asyncpg.connect(os.environ["IMPORT_TARGET_DSN"])
    report: dict[str, object] = {"tenant_slug": TENANT_SLUG}
    try:
        await src.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        tenant = await src.fetchrow(
            "SELECT id, name, slug, status, is_deleted, created_at, updated_at"
            " FROM public.tenants WHERE slug = $1",
            TENANT_SLUG,
        )
        if tenant is None:
            raise SystemExit(f"Source tenant {TENANT_SLUG!r} not found")
        tid = tenant["id"]
        users = await src.fetch(
            "SELECT id, tenant_id, email, password_hash, display_name, is_active, is_deleted,"
            " created_at, updated_at FROM public.users WHERE tenant_id = $1",
            tid,
        )
        roles = await src.fetch(
            "SELECT id, tenant_id, name, description, is_deleted, created_at, updated_at"
            " FROM public.roles WHERE tenant_id = $1",
            tid,
        )
        permissions = await src.fetch("SELECT id, code, description FROM public.permissions")
        role_permissions = await src.fetch(
            "SELECT role_id, permission_id, tenant_id FROM public.role_permissions"
            " WHERE tenant_id = $1",
            tid,
        )
        user_roles = await src.fetch(
            "SELECT user_id, role_id, tenant_id FROM public.user_roles WHERE tenant_id = $1", tid
        )
        jurisdictions = await src.fetch(
            "SELECT id, canonical_code, name, jurisdiction_type, parent_id, status"
            " FROM tax.jurisdictions ORDER BY (parent_id IS NOT NULL), canonical_code"
        )
        providers = await src.fetch(
            "SELECT id, code, display_name, supports_api, supports_file, status"
            " FROM payroll.providers ORDER BY code"
        )

        inserted: dict[str, int] = {}

        async def run(key: str, sql: str, rows: list[tuple[object, ...]]) -> None:
            count = 0
            for row in rows:
                status = await dst.execute(sql, *row)
                count += int(status.split()[-1])
            inserted[key] = count

        async with dst.transaction():
            await run(
                "tenants",
                "INSERT INTO tenants (id, name, slug, status, is_deleted, created_at, updated_at)"
                " VALUES ($1,$2,$3,$4,$5,$6,$7) ON CONFLICT DO NOTHING",
                [tuple(tenant.values())],
            )
            await run(
                "permissions",
                "INSERT INTO permissions (id, code, description) VALUES ($1,$2,$3)"
                " ON CONFLICT DO NOTHING",
                [tuple(r.values()) for r in permissions],
            )
            await run(
                "users",
                "INSERT INTO users (id, tenant_id, email, password_hash, display_name, is_active,"
                " is_deleted, created_at, updated_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)"
                " ON CONFLICT DO NOTHING",
                [tuple(r.values()) for r in users],
            )
            await run(
                "roles",
                "INSERT INTO roles (id, tenant_id, name, description, is_deleted, created_at,"
                " updated_at) VALUES ($1,$2,$3,$4,$5,$6,$7) ON CONFLICT DO NOTHING",
                [tuple(r.values()) for r in roles],
            )
            # Permission IDs may differ if the target catalog already had the code.
            target_perm = {
                r["code"]: r["id"] for r in await dst.fetch("SELECT id, code FROM permissions")
            }
            source_perm_code = {r["id"]: r["code"] for r in permissions}
            await run(
                "role_permissions",
                "INSERT INTO role_permissions (role_id, permission_id, tenant_id) VALUES ($1,$2,$3)"
                " ON CONFLICT DO NOTHING",
                [
                    (
                        r["role_id"],
                        target_perm[source_perm_code[r["permission_id"]]],
                        r["tenant_id"],
                    )
                    for r in role_permissions
                ],
            )
            await run(
                "user_roles",
                "INSERT INTO user_roles (user_id, role_id, tenant_id) VALUES ($1,$2,$3)"
                " ON CONFLICT DO NOTHING",
                [tuple(r.values()) for r in user_roles],
            )
            await run(
                "tax_jurisdictions",
                "INSERT INTO tax_jurisdictions (id, tenant_id, code, name, level, country_code,"
                " parent_id, active) VALUES ($1,$2,$3,$4,$5,'US',$6,$7) ON CONFLICT DO NOTHING",
                [
                    (
                        r["id"],
                        tid,
                        r["canonical_code"],
                        r["name"],
                        r["jurisdiction_type"],
                        r["parent_id"],
                        r["status"] == "active",
                    )
                    for r in jurisdictions
                ],
            )
            await run(
                "integrations_provider_definitions",
                "INSERT INTO integrations_provider_definitions (id, tenant_id, status, code, name,"
                " description, data) VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb) ON CONFLICT DO NOTHING",
                [
                    (
                        r["id"],
                        tid,
                        r["status"],
                        r["code"],
                        r["display_name"],
                        "Payroll import provider (imported from the recovered database)",
                        json.dumps(
                            {
                                "category": "payroll_import",
                                "supports_api": r["supports_api"],
                                "supports_file": r["supports_file"],
                                "legacy_source": "forgeflow.payroll.providers",
                                "legacy_source_id": str(r["id"]),
                            }
                        ),
                    )
                    for r in providers
                ],
            )

        # Reconciliation: target counts for the tenant must equal source counts.
        async def target_count(sql: str) -> int:
            return int(await dst.fetchval(sql, tid))

        source = {
            "tenants": 1,
            "users": len(users),
            "roles": len(roles),
            "role_permissions": len(role_permissions),
            "user_roles": len(user_roles),
            "tax_jurisdictions": len(jurisdictions),
            "integrations_provider_definitions": len(providers),
        }
        target = {
            "tenants": await target_count("SELECT count(*) FROM tenants WHERE id = $1"),
            "users": await target_count("SELECT count(*) FROM users WHERE tenant_id = $1"),
            "roles": await target_count("SELECT count(*) FROM roles WHERE tenant_id = $1"),
            "role_permissions": await target_count(
                "SELECT count(*) FROM role_permissions WHERE tenant_id = $1"
            ),
            "user_roles": await target_count(
                "SELECT count(*) FROM user_roles WHERE tenant_id = $1"
            ),
            "tax_jurisdictions": await target_count(
                "SELECT count(*) FROM tax_jurisdictions WHERE tenant_id = $1"
            ),
            "integrations_provider_definitions": await target_count(
                "SELECT count(*) FROM integrations_provider_definitions WHERE tenant_id = $1"
            ),
        }
        hashes_match = True
        for u in users:
            same = await dst.fetchval(
                "SELECT password_hash = $2 FROM users WHERE id = $1", u["id"], u["password_hash"]
            )
            hashes_match = hashes_match and bool(same)
        permission_codes_present = all(r["code"] in target_perm for r in permissions)
        report.update(
            {
                "source_counts": source,
                "target_counts": target,
                "inserted_this_run": inserted,
                "password_hashes_match_source": hashes_match,
                "permission_codes_present": permission_codes_present,
                "reconciled": source == target and hashes_match and permission_codes_present,
                "not_imported": {
                    "legacy_test_organizations": "archived in recovered database",
                    "legacy_identity_users": "archived in recovered database",
                },
            }
        )
    finally:
        await src.close()
        await dst.close()
    print(json.dumps(report, indent=2, default=str))
    return 0 if report.get("reconciled") else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

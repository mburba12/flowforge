from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPORT_PATH = Path("var/complete_api_database_install_report.json")
TEST_STATUS = "complete_api_rls_test"


def run_psql(sql: str) -> list[str]:
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "psql",
         "-P", "pager=off", "-v", "ON_ERROR_STOP=1", "-U", "flowforge",
         "-d", "flowforge", "-tA", "-F", "|", "-c", sql],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("PostgreSQL command failed:\n" + result.stderr + "\n" + result.stdout)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def count_queries(tables: list[str], tenant_id: str | None = None) -> str:
    statements = []
    for table in tables:
        where = f"status = '{TEST_STATUS}'"
        if tenant_id:
            where += f" AND tenant_id = '{tenant_id}'::uuid"
        statements.append(f'SELECT \'{table}\', COUNT(*) FROM "{table}" WHERE {where};')
    return "\n".join(statements)


def parse_counts(lines: list[str], table_set: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        if "|" not in line:
            continue
        table, value = line.rsplit("|", 1)
        if table in table_set:
            counts[table] = int(value)
    return counts


def main() -> int:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8-sig"))
    tables = sorted({str(x).strip() for x in report["new_tables"] if str(x).strip()})
    table_set = set(tables)
    if len(tables) != 289:
        raise RuntimeError(f"Expected 289 tables; found {len(tables)}")

    tenant_ids = run_psql("SELECT DISTINCT tenant_id::text FROM users WHERE tenant_id IS NOT NULL ORDER BY tenant_id::text LIMIT 2;")
    if len(tenant_ids) != 2:
        raise RuntimeError(f"Exactly two populated tenants are required; found {len(tenant_ids)}")
    tenant_a, tenant_b = tenant_ids
    if tenant_a == tenant_b:
        raise RuntimeError("Owner and attacker tenant IDs must differ")

    print(f"OWNER TENANT:    {tenant_a}")
    print(f"ATTACKER TENANT: {tenant_b}")

    cleanup_sql = "\n".join(f'DELETE FROM "{t}" WHERE status = \'{TEST_STATUS}\';' for t in tables)
    run_psql("BEGIN;\n" + cleanup_sql + "\nCOMMIT;")

    insert_sql = "\n".join(
        f'INSERT INTO "{t}" (tenant_id, status, code, name, data) VALUES '
        f"('{tenant_a}'::uuid, '{TEST_STATUS}', 'rls-test-{t}', "
        f"'Temporary RLS test', '{{\"temporary\": true}}'::jsonb);"
        for t in tables
    )
    run_psql("BEGIN;\n" + insert_sql + "\nCOMMIT;")
    print("INSERTED: one owner record in each of 289 tables")

    try:
        queries = count_queries(tables, tenant_a)
        attacker = run_psql(
            "BEGIN;\nSET LOCAL ROLE flowforge_app;\n"
            f"SELECT set_config('app.current_tenant_id', '{tenant_b}', true);\n"
            + queries + "\nROLLBACK;"
        )
        attacker_counts = parse_counts(attacker, table_set)
        if len(attacker_counts) != 289:
            raise RuntimeError(f"Expected 289 attacker results; found {len(attacker_counts)}")
        leaks = {k: v for k, v in attacker_counts.items() if v != 0}
        if leaks:
            raise RuntimeError("Cross-tenant records visible:\n" + "\n".join(f"{k}|{v}" for k, v in leaks.items()))
        print("PASSED: ATTACKER SEES ZERO RECORDS ACROSS 289 TABLES")

        owner = run_psql(
            "BEGIN;\nSET LOCAL ROLE flowforge_app;\n"
            f"SELECT set_config('app.current_tenant_id', '{tenant_a}', true);\n"
            + queries + "\nROLLBACK;"
        )
        owner_counts = parse_counts(owner, table_set)
        if len(owner_counts) != 289:
            raise RuntimeError(f"Expected 289 owner results; found {len(owner_counts)}")
        wrong = {k: v for k, v in owner_counts.items() if v != 1}
        if wrong:
            raise RuntimeError("Owner visibility incorrect:\n" + "\n".join(f"{k}|{v}" for k, v in wrong.items()))
        print("PASSED: OWNER SEES ALL 289 RECORDS")
    finally:
        run_psql("BEGIN;\n" + cleanup_sql + "\nCOMMIT;")

    remaining = parse_counts(run_psql(count_queries(tables)), table_set)
    if len(remaining) != 289:
        raise RuntimeError(f"Expected 289 cleanup results; found {len(remaining)}")
    not_removed = {k: v for k, v in remaining.items() if v != 0}
    if not_removed:
        raise RuntimeError("Temporary records remain:\n" + "\n".join(f"{k}|{v}" for k, v in not_removed.items()))

    print("PASSED: 289-TABLE TEST DATA CLEANUP")
    print("FLOWFORGE COMPLETE-PLATFORM TENANT ISOLATION PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise

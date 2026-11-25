import subprocess
from pathlib import Path

from flowforge.security_hardening.rls import rls_sql

TENANT_TABLE_QUERY = """
SELECT t.table_name
FROM information_schema.tables AS t
WHERE t.table_schema = 'public'
  AND EXISTS (
      SELECT 1
      FROM information_schema.columns AS c
      WHERE c.table_schema = t.table_schema
        AND c.table_name = t.table_name
        AND c.column_name = 'tenant_id'
  )
ORDER BY t.table_name;
"""


def load_tenant_tables() -> list[str]:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "flowforge",
            "-d",
            "flowforge",
            "-tA",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            TENANT_TABLE_QUERY,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    tables = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    if not tables:
        raise RuntimeError("No tenant-owned tables were found.")

    if len(tables) != len(set(tables)):
        raise RuntimeError("Duplicate tenant-table names were returned.")

    return tables


def main() -> None:
    tables = load_tenant_tables()

    output_path = Path("var/tenant_rls.sql")
    output_path.parent.mkdir(exist_ok=True)

    policy_sql = "\n\n".join(rls_sql(table_name) for table_name in tables)

    output_path.write_text(
        policy_sql + "\n",
        encoding="utf-8",
    )

    inventory_path = Path("var/tenant_rls_tables.txt")
    inventory_path.write_text(
        "\n".join(tables) + "\n",
        encoding="utf-8",
    )

    print(f"Generated forced RLS for {len(tables)} tenant tables.")
    print(f"Policy file: {output_path}")
    print(f"Inventory file: {inventory_path}")


if __name__ == "__main__":
    main()

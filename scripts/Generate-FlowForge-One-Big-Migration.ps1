$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\mackb\Downloads\Download the FlowForge Phase 1 scaffold\flowforge-phase1"
Set-Location $ProjectRoot

$Python = ".\.venv\Scripts\python.exe"
$ReportPath = ".\var\complete_api_database_install_report.json"
$MigrationPath = ".\migrations\versions\ff_all_apis_delta_001_complete_platform_schema.py"

foreach ($Path in @($Python, $ReportPath, ".\migrations\versions")) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing required path: $Path" }
}

$Report = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json
$NewTables = @($Report.new_tables | ForEach-Object { "$($_)".Trim() } | Where-Object { $_ } | Sort-Object -Unique)
$Collisions = @($Report.collisions | ForEach-Object { "$($_)".Trim() } | Where-Object { $_ } | Sort-Object -Unique)

if ($NewTables.Count -ne 289) { throw "Expected 289 net-new tables; found $($NewTables.Count)." }
$Overlap = @($NewTables | Where-Object { $_ -in $Collisions })
if ($Overlap.Count) { $Overlap; throw "Net-new inventory overlaps collisions." }
$Invalid = @($NewTables | Where-Object { $_ -notmatch '^[a-z][a-z0-9_]{0,62}$' })
if ($Invalid.Count) { $Invalid; throw "Invalid PostgreSQL table names detected." }

$env:FLOWFORGE_NEW_TABLES_JSON = $NewTables | ConvertTo-Json -Compress
$env:FLOWFORGE_MIGRATION_PATH = Join-Path $ProjectRoot $MigrationPath

$GeneratorPath = ".\var\generate_one_big_migration.py"
@'
from __future__ import annotations

import json
import os
from pathlib import Path

path = Path(os.environ["FLOWFORGE_MIGRATION_PATH"])
tables = json.loads(os.environ["FLOWFORGE_NEW_TABLES_JSON"])
if len(tables) != 289 or len(tables) != len(set(tables)):
    raise RuntimeError("The migration inventory must contain 289 unique tables")

template = r'''"""Create 289 net-new complete-platform tables.

Revision ID: ff_all_apis_delta_001
Revises: f174aad30e21
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "ff_all_apis_delta_001"
down_revision = "f174aad30e21"
branch_labels = None
depends_on = None

TABLES = __TABLES__


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names(schema="public"))
    unexpected = sorted(existing.intersection(TABLES))
    if unexpected:
        raise RuntimeError(
            "Migration refused because proposed net-new tables already exist: "
            + ", ".join(unexpected)
        )

    for table in TABLES:
        op.create_table(
            table,
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "tenant_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "status",
                sa.String(length=64),
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
            sa.Column("code", sa.String(length=160), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "data",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "version",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            ),
            sa.Column(
                "is_archived",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint("version >= 1", name=f"ck_{table}_version"),
            sa.UniqueConstraint(
                "tenant_id",
                "code",
                name=f"uq_{table}_tenant_code",
            ),
        )
        op.create_index(
            f"ix_{table}_tenant_status",
            table,
            ["tenant_id", "status"],
        )
        op.create_index(
            f"ix_{table}_tenant_archived",
            table,
            ["tenant_id", "is_archived"],
        )
        op.execute(
            sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        )
        op.execute(
            sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
        )
        policy_sql = (
            f'CREATE POLICY "{table}_tenant_isolation" ON "{table}" '
            "FOR ALL "
            "USING (tenant_id = NULLIF("
            "current_setting('app.current_tenant_id', true), ''"
            ")::uuid) "
            "WITH CHECK (tenant_id = NULLIF("
            "current_setting('app.current_tenant_id', true), ''"
            ")::uuid)"
        )
        op.execute(sa.text(policy_sql))
        op.execute(
            sa.text(
                f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE '
                f'"{table}" TO flowforge_app'
            )
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_table(table)
'''

path.write_text(template.replace("__TABLES__", repr(tables)), encoding="utf-8")
print(path)
'@ | Set-Content -LiteralPath $GeneratorPath -Encoding UTF8

& $Python $GeneratorPath
if ($LASTEXITCODE -ne 0) { throw "Migration generation failed." }

& $Python -m ruff format $MigrationPath
if ($LASTEXITCODE -ne 0) { throw "Migration formatting failed." }
& $Python -m ruff check $MigrationPath --fix
if ($LASTEXITCODE -ne 0) { throw "Migration Ruff validation failed." }
& $Python -m py_compile $MigrationPath
if ($LASTEXITCODE -ne 0) { throw "Migration compilation failed." }

$env:FLOWFORGE_MIGRATION_PATH = (Resolve-Path $MigrationPath).Path
$AuditPath = ".\var\audit_one_big_migration.py"
@'
from __future__ import annotations

import ast
import os
from pathlib import Path

path = Path(os.environ["FLOWFORGE_MIGRATION_PATH"])
text = path.read_text(encoding="utf-8")
tree = ast.parse(text, filename=str(path))
assignments = {
    node.targets[0].id: node.value
    for node in tree.body
    if isinstance(node, ast.Assign)
    and len(node.targets) == 1
    and isinstance(node.targets[0], ast.Name)
}
tables = ast.literal_eval(assignments["TABLES"])
revision = ast.literal_eval(assignments["revision"])
down_revision = ast.literal_eval(assignments["down_revision"])
if len(tables) != 289 or len(tables) != len(set(tables)):
    raise RuntimeError("Migration does not contain 289 unique tables")
if revision != "ff_all_apis_delta_001":
    raise RuntimeError("Unexpected revision")
if down_revision != "f174aad30e21":
    raise RuntimeError("Unexpected down revision")
for marker in (
    "ENABLE ROW LEVEL SECURITY",
    "FORCE ROW LEVEL SECURITY",
    "CREATE POLICY",
    "app.current_tenant_id",
    "flowforge_app",
    "def downgrade()",
):
    if marker not in text:
        raise RuntimeError(f"Missing marker: {marker}")
print("PASSED: one migration, 289 unique tables, forced RLS, grants, downgrade")
'@ | Set-Content -LiteralPath $AuditPath -Encoding UTF8

& $Python $AuditPath
if ($LASTEXITCODE -ne 0) { throw "Migration structural audit failed." }

$Heads = @(& $Python -m alembic heads)
if ($LASTEXITCODE -ne 0) { throw "Alembic heads check failed." }
if (($Heads -join "`n") -notmatch "ff_all_apis_delta_001") {
    $Heads
    throw "The new migration is not the Alembic head."
}

Write-Host ""
Write-Host "ONE BIG FLOWFORGE MIGRATION GENERATED" -ForegroundColor Green
Write-Host "Migration: $MigrationPath"
Write-Host "Tables:    289"
Write-Host "Revision:  ff_all_apis_delta_001"
Write-Host "Applied:   No"

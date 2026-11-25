param(
    [switch]$CreateCheckpoints
)

$ErrorActionPreference = "Stop"
$Python = ".\.venv\Scripts\python.exe"
$AlembicPath = ".\migrations\env.py"
$BackupPath = ".\migrations\env.py.phase4e4j.backup"
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

$Waves = @(
    @{ Code="4e"; Message="phase 4e reconciliation"; Tables=8; Public=206; Rls=202; Tag="v4.4.0-phase4e-reconciliation" },
    @{ Code="4f"; Message="phase 4f copilot documents"; Tables=10; Public=216; Rls=212; Tag="v4.5.0-phase4f-copilot-documents" },
    @{ Code="4g"; Message="phase 4g governed automation"; Tables=10; Public=226; Rls=222; Tag="v4.6.0-phase4g-governed-automation" },
    @{ Code="4h"; Message="phase 4h enterprise controls"; Tables=6; Public=232; Rls=228; Tag="v4.7.0-phase4h-enterprise-controls" },
    @{ Code="4i"; Message="phase 4i production activation controls"; Tables=6; Public=238; Rls=234; Tag="v4.8.0-phase4i-production-connectors" },
    @{ Code="4j"; Message="phase 4j release candidate"; Tables=4; Public=242; Rls=238; Tag="v4.9.0-phase4j-release-candidate" }
)

function Invoke-Gate {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "RUNNING: $Name" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
    Write-Host "PASSED: $Name" -ForegroundColor Green
}

function Restore-Alembic {
    if (Test-Path -LiteralPath $BackupPath) {
        Copy-Item -LiteralPath $BackupPath -Destination $AlembicPath -Force
        Remove-Item -LiteralPath $BackupPath -Force
    }
}

function Get-ManifestTables {
    param([string]$Code)
    $Manifest = Get-Content ".\manifests\phase$Code.json" -Raw | ConvertFrom-Json
    return @($Manifest.tables)
}

function Set-IsolatedAlembicMetadata {
    param([string]$Code)

    $Full = [System.IO.File]::ReadAllText(
        (Resolve-Path $BackupPath)
    )

    $BaseLines = @(
        $Full -split "`r?`n" |
            Where-Object {
                $_ -notmatch (
                    '^from flowforge\.phase4[e-j] ' +
                    'import models as phase4[e-j]_models'
                )
            }
    )

    $WaveOrder = @(
        "4e",
        "4f",
        "4g",
        "4h",
        "4i",
        "4j"
    )

    $CurrentIndex = [Array]::IndexOf(
        $WaveOrder,
        $Code
    )

    if ($CurrentIndex -lt 0) {
        throw "Unknown Phase 4 wave: $Code"
    }

    $CumulativeWaves = @(
        $WaveOrder[0..$CurrentIndex]
    )

    $Imports = @(
        foreach ($WaveCode in $CumulativeWaves) {
            (
                "from flowforge.phase$WaveCode " +
                "import models as " +
                "phase${WaveCode}_models " +
                "# noqa: F401"
            )
        }
    )

    $MetadataText = (
        ($Imports -join "`r`n") +
        "`r`n" +
        ($BaseLines -join "`r`n")
    )

    [System.IO.File]::WriteAllText(
        (Resolve-Path $AlembicPath),
        $MetadataText,
        $Utf8NoBom
    )

    Write-Host (
        "CUMULATIVE METADATA: " +
        ($CumulativeWaves -join ", ")
    ) -ForegroundColor Cyan
}

function Test-MigrationAst {
    param([string]$MigrationPath, [string[]]$ExpectedTables)
    $env:PHASE4_MIGRATION = $MigrationPath
    $env:PHASE4_TABLES = ($ExpectedTables | ConvertTo-Json -Compress)
    $Audit = @"
import ast, json, os
from pathlib import Path
path = Path(os.environ['PHASE4_MIGRATION'])
expected = set(json.loads(os.environ['PHASE4_TABLES']))
tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
upgrade, downgrade = functions.get('upgrade'), functions.get('downgrade')
if upgrade is None or downgrade is None:
    raise RuntimeError('Missing upgrade/downgrade')
def calls(fn, name):
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'op' and n.func.attr == name]
def first(call):
    return call.args[0].value if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str) else None
creates = calls(upgrade, 'create_table')
created = {x for c in creates if (x := first(c))}
upgrade_drops = calls(upgrade, 'drop_table')
dropped = {x for c in calls(downgrade, 'drop_table') if (x := first(c))}
tenant = set()
for call in creates:
    table = first(call)
    for arg in call.args[1:]:
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == 'Column' and arg.args and isinstance(arg.args[0], ast.Constant) and arg.args[0].value == 'tenant_id':
            tenant.add(table)
print('Created:', sorted(created))
if created != expected: raise RuntimeError(f'Table mismatch missing={sorted(expected-created)} extra={sorted(created-expected)}')
if tenant != expected: raise RuntimeError(f'Missing tenant_id: {sorted(expected-tenant)}')
if upgrade_drops: raise RuntimeError('upgrade contains drop_table')
if dropped != expected: raise RuntimeError('downgrade table mismatch')
print('PASSED: migration AST audit')
"@
    $Audit | & $Python -
    if ($LASTEXITCODE -ne 0) { throw "Migration AST audit failed" }
}

$Phase4DTag = "v4.3.0-phase4d-unified-data"
$Phase4DCommit = "$(git rev-list -n 1 $Phase4DTag)".Trim()
if (-not $Phase4DCommit) { throw "Missing Phase 4D tag: $Phase4DTag" }
git merge-base --is-ancestor $Phase4DCommit HEAD
if ($LASTEXITCODE -ne 0) { throw "Current HEAD does not descend from the Phase 4D checkpoint" }
if (git status --porcelain) { throw "Working tree must be clean before continuous installation" }

Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:\FLOWFORGE_DATABASE_URL -ErrorAction SilentlyContinue
Invoke-Gate "Owner role" { & $Python -c "from flowforge.core.config import settings; from sqlalchemy.engine import make_url; u=make_url(settings.database_url); print(u.username); assert u.username=='flowforge'" }
Invoke-Gate "Single Alembic head" { & $Python -c "import subprocess; x=subprocess.check_output(['.\\.venv\\Scripts\\python.exe','-m','alembic','heads'], text=True); assert len([a for a in x.splitlines() if a.strip()])==1; print(x.strip())" }

Copy-Item -LiteralPath $AlembicPath -Destination $BackupPath -Force
try {
    foreach ($Wave in $Waves) {
        $Code = $Wave.Code
        $Upper = $Code.ToUpper()
        $Tables = Get-ManifestTables $Code

        $QuotedInstalledTables = (
            $Tables |
                ForEach-Object {
                    "'$_'"
                }
        ) -join ","

        $InstalledTableCount = docker compose exec -T postgres psql `
            -P pager=off `
            -U flowforge `
            -d flowforge `
            -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ($QuotedInstalledTables);"

        if ($LASTEXITCODE -ne 0) {
            throw "Phase $Upper installation-state query failed."
        }

        $InstalledTableCount = (
            "$InstalledTableCount"
        ).Trim()

        if (
            $InstalledTableCount -eq
            "$($Tables.Count)"
        ) {
            Write-Host (
                "SKIPPING PHASE ${Upper}: " +
                "all expected tables are installed."
            ) -ForegroundColor Yellow

            continue
        }

        if ($InstalledTableCount -ne "0") {
            throw (
                "Phase $Upper is partially installed: " +
                "$InstalledTableCount of " +
                "$($Tables.Count) tables."
            )
        }
        if ($Tables.Count -ne $Wave.Tables) { throw "$Upper manifest expected $($Wave.Tables) tables, found $($Tables.Count)" }
        Write-Host "`n===== INSTALLING PHASE $Upper =====" -ForegroundColor Yellow
        Set-IsolatedAlembicMetadata $Code
        Invoke-Gate "$Upper Alembic lint" { & $Python -m ruff check $AlembicPath --fix }
        $Before = @(Get-ChildItem .\migrations\versions -File | Select-Object -ExpandProperty FullName)
        Invoke-Gate "$Upper migration generation" { & $Python -m alembic revision --autogenerate -m $Wave.Message }
        $After = @(Get-ChildItem .\migrations\versions -File | Select-Object -ExpandProperty FullName)
        $New = @($After | Where-Object { $_ -notin $Before })
        if ($New.Count -ne 1) { throw "$Upper expected one migration, found $($New.Count)" }
        Test-MigrationAst $New[0] $Tables
        Invoke-Gate "$Upper migration format" { & $Python -m ruff format $New[0] }
        Invoke-Gate "$Upper migration lint" { & $Python -m ruff check $New[0] --fix }
        Invoke-Gate "$Upper migration compile" { & $Python -m py_compile $New[0] }
        Invoke-Gate "$Upper upgrade" { & $Python -m alembic upgrade head }
        $GrantSql = "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE " + ($Tables -join ',') + " TO flowforge_app;"
        $GrantSql | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U flowforge -d flowforge
        if ($LASTEXITCODE -ne 0) { throw "$Upper grants failed" }
        Invoke-Gate "$Upper RLS generation" { & $Python .\scripts\Generate-Tenant-RLS.py }
        Get-Content .\var\tenant_rls.sql -Raw | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U flowforge -d flowforge
        if ($LASTEXITCODE -ne 0) { throw "$Upper RLS apply failed" }
        $Quoted = ($Tables | ForEach-Object { "'$_'" }) -join ','
        $WaveRls = "$(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT COUNT(*) FILTER (WHERE c.relrowsecurity AND c.relforcerowsecurity),COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname IN ($Quoted);")".Trim()
        if ($WaveRls -ne "$($Tables.Count)|$($Tables.Count)") { throw "$Upper RLS mismatch: $WaveRls" }
        $Public = "$(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")".Trim()
        $Rls = "$(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity AND c.relforcerowsecurity;")".Trim()
        if ($Public -ne "$($Wave.Public)") { throw "$Upper expected $($Wave.Public) public tables, found $Public" }
        if ($Rls -ne "$($Wave.Rls)") { throw "$Upper expected $($Wave.Rls) forced-RLS tables, found $Rls" }
        Invoke-Gate "$Upper focused tests" { & $Python -m pytest -q ".\tests\phase$Code" }
        Invoke-Gate "$Upper full regression" { & $Python -m pytest -q }
        if ($CreateCheckpoints) {
            Restore-Alembic
            git add .
            git commit -m "Complete Phase $Upper"
            if ($LASTEXITCODE -ne 0) { throw "$Upper commit failed" }
            git tag -a $Wave.Tag -m "Phase $Upper complete"
            if ($LASTEXITCODE -ne 0) { throw "$Upper tag failed" }
            Copy-Item -LiteralPath $AlembicPath -Destination $BackupPath -Force
        }
        Write-Host "PHASE $Upper CHECKPOINT PASSED" -ForegroundColor Green
    }
}
finally {
    Restore-Alembic
}

$FinalCheckPaths = @(
    ".\src",
    ".\tests",
    ".\migrations\env.py"
)

Invoke-Gate "Final Ruff" {
    & $Python -m ruff check $FinalCheckPaths
}

Invoke-Gate "Final format" {
    & $Python -m ruff format --check $FinalCheckPaths
}

Invoke-Gate "Final compile" {
    & $Python -m compileall -q ".\src" ".\tests"
}

Invoke-Gate "Final tests" {
    & $Python -m pytest -q
}

if ($CreateCheckpoints) {
    $FinalTag = "v4.9.0-phase4-complete"
    git tag -a $FinalTag -m "FlowForge Phase 4 complete"
    if ($LASTEXITCODE -ne 0) { throw "Final Phase 4 tag failed" }
}
Write-Host "FLOWFORGE PHASE 4E-4J CONTINUOUS INSTALLATION PASSED" -ForegroundColor Green


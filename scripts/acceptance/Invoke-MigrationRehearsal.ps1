[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Timestamp = Get-Date -Format "yyyyMMddHHmmss"
$Database = "flowforge_migration_rehearsal_$Timestamp"
$TempConfig = Join-Path $env:TEMP "flowforge-alembic-$Timestamp.ini"
$Created = $false
$PreviousDatabaseUrl = [Environment]::GetEnvironmentVariable("DATABASE_URL", "Process")
$DisposableDatabaseUrl = "postgresql+asyncpg://flowforge:flowforge@localhost:5433/$Database"

try {
    docker compose exec -T postgres createdb -U flowforge $Database
    if ($LASTEXITCODE -ne 0) { throw "Unable to create disposable database." }
    $Created = $true

    $Config = [IO.File]::ReadAllText((Join-Path $ProjectRoot "alembic.ini"))
    $Config = [Text.RegularExpressions.Regex]::Replace(
        $Config,
        '(?m)^sqlalchemy\.url\s*=\s*.+$',
        "sqlalchemy.url = postgresql+asyncpg://flowforge:flowforge@localhost:5433/$Database",
        1
    )
    [IO.File]::WriteAllText($TempConfig, $Config, (New-Object Text.UTF8Encoding($false)))

    # env.py reads DATABASE_URL and otherwise overrides sqlalchemy.url from the temporary INI.
    $env:DATABASE_URL = $DisposableDatabaseUrl

    Write-Host "RUNNING: Upgrade disposable database" -ForegroundColor Cyan
    & $Python -m alembic -c $TempConfig upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Disposable upgrade failed." }

    $Head = (docker compose exec -T postgres psql -U flowforge -d $Database -At -v ON_ERROR_STOP=1 -c "SELECT version_num FROM alembic_version;").Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Head)) { throw "Unable to read disposable head." }

    $HeadTables = (docker compose exec -T postgres psql -U flowforge -d $Database -At -v ON_ERROR_STOP=1 -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';").Trim()
    if ($LASTEXITCODE -ne 0 -or [int]$HeadTables -le 0) { throw "Disposable database has no application tables." }

    Write-Host "RUNNING: Downgrade one revision" -ForegroundColor Cyan
    & $Python -m alembic -c $TempConfig downgrade -1
    if ($LASTEXITCODE -ne 0) { throw "Disposable downgrade failed." }

    $Down = (docker compose exec -T postgres psql -U flowforge -d $Database -At -v ON_ERROR_STOP=1 -c "SELECT version_num FROM alembic_version;").Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Down) -or $Down -eq $Head) { throw "Downgrade did not move away from head." }

    Write-Host "RUNNING: Re-upgrade to head" -ForegroundColor Cyan
    & $Python -m alembic -c $TempConfig upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Disposable re-upgrade failed." }

    $Final = (docker compose exec -T postgres psql -U flowforge -d $Database -At -v ON_ERROR_STOP=1 -c "SELECT version_num FROM alembic_version;").Trim()
    if ($LASTEXITCODE -ne 0 -or $Final -ne $Head) { throw "Final revision mismatch. Expected=$Head Actual=$Final" }

    $FinalTables = (docker compose exec -T postgres psql -U flowforge -d $Database -At -v ON_ERROR_STOP=1 -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';").Trim()
    if ($LASTEXITCODE -ne 0 -or $FinalTables -ne $HeadTables) { throw "Final table count mismatch. Expected=$HeadTables Actual=$FinalTables" }

    $RlsSql = "WITH t AS (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id'), p AS (SELECT tablename,COUNT(*) AS n FROM pg_policies WHERE schemaname='public' GROUP BY tablename) SELECT COUNT(*) FROM t JOIN pg_class c ON c.relname=t.table_name JOIN pg_namespace n ON n.oid=c.relnamespace AND n.nspname='public' LEFT JOIN p ON p.tablename=t.table_name WHERE NOT c.relrowsecurity OR NOT c.relforcerowsecurity OR COALESCE(p.n,0)<1;"
    $RlsFailures = (docker compose exec -T postgres psql -U flowforge -d $Database -At -v ON_ERROR_STOP=1 -c $RlsSql).Trim()
    if ($LASTEXITCODE -ne 0 -or $RlsFailures -ne "0") { throw "RLS validation failed for $RlsFailures tenant tables." }

    Write-Host "FLOWFORGE MIGRATION REHEARSAL PASSED" -ForegroundColor Green
    Write-Host "Head revision: $Final"
    Write-Host "Table count: $FinalTables"
    Write-Host "RLS failures: $RlsFailures"
}
finally {
    if ($null -eq $PreviousDatabaseUrl) { Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue } else { $env:DATABASE_URL = $PreviousDatabaseUrl }
    if (Test-Path -LiteralPath $TempConfig) { Remove-Item -LiteralPath $TempConfig -Force }
    if ($Created) {
        docker compose exec -T postgres dropdb -U flowforge --force --if-exists $Database | Out-Null
    }
}

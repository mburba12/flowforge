<#
.SYNOPSIS
    Rerun the existing FlowForge acceptance gates against an ISOLATED database and API.

.DESCRIPTION
    Never touches the recovered forgeflow database or the live API on :8000.
      - Database: compose service "postgres" (flowforge-phase1-postgres-1, host port 5433), database "flowforge",
        migrated to Alembic head from the repository's migration chain.
      - API: a separate container (flowforge-acceptance-api, host port 8001) from the current API image,
        connecting as the restricted flowforge_app role.
    Each gate runs independently; failures are recorded and the run continues.
    Results: var\acceptance-rerun\<timestamp>\results.json, summary.txt, one log per gate.

    The flowforge_app password is read from COMPOSE_APP_DATABASE_URL in .env.phase-c (gitignored) and never printed.
#>
[CmdletBinding()]
param(
    [int]$IsolatedApiPort = 8001,
    [int]$Phase4Port = 8002,
    [switch]$KeepIsolatedApi
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 3.0
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Out = Join-Path $Root "var\acceptance-rerun\$Stamp"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$PgContainer = "flowforge-phase1-postgres-1"
$ApiContainer = "flowforge-acceptance-api"
$Api = "http://127.0.0.1:$IsolatedApiPort"
$Results = New-Object System.Collections.Generic.List[object]

# Safety: the isolated database must be the compose "postgres" service, never the recovered DB.
$labelsJson = docker inspect $PgContainer --format '{{json .Config.Labels}}'
if ($LASTEXITCODE -ne 0) { throw "Isolated Postgres container not found." }
$svc = ($labelsJson | ConvertFrom-Json).'com.docker.compose.service'
if ($svc -ne "postgres") { throw "Isolated Postgres container is not the compose postgres service (got '$svc')." }

# Restricted role password (from gitignored .env)
$appUrlMatch = Select-String -Path (Join-Path $Root ".env.phase-c") -Pattern '^COMPOSE_APP_DATABASE_URL=(.+)$'
if (-not $appUrlMatch) { throw "COMPOSE_APP_DATABASE_URL missing from .env.phase-c" }
$AppUrlInDocker = $appUrlMatch.Matches[0].Groups[1].Value.Trim()
$RuntimePassword = [uri]::UnescapeDataString(([uri]($AppUrlInDocker -replace '^postgresql\+asyncpg', 'postgresql')).UserInfo.Split(':', 2)[1])
$AppUrlOnHost = $AppUrlInDocker -replace '@postgres:5432/', '@localhost:5433/'

function Invoke-Gate {
    param([string]$Id, [string]$Name, [scriptblock]$Action)
    $log = Join-Path $Out "$Id.log"
    $start = Get-Date
    Write-Host "RUNNING  $Id $Name" -ForegroundColor Cyan
    $status = "PASS"; $detail = ""
    try {
        $global:LASTEXITCODE = 0
        $ErrorActionPreference = "Continue"
        & $Action *>&1 | ForEach-Object { "$_" } | Out-File -FilePath $log -Encoding utf8
        $code = $LASTEXITCODE
        $ErrorActionPreference = "Stop"
        if ($code -ne 0) { $status = "FAIL"; $detail = "exit code $code" }
    } catch {
        $ErrorActionPreference = "Stop"
        $status = "FAIL"; $detail = $_.Exception.Message
        Add-Content -Path $log -Value "EXCEPTION: $detail" -Encoding utf8
    }
    $secs = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
    $tail = (Get-Content $log -Tail 3 -ErrorAction SilentlyContinue) -join " | "
    $Results.Add([pscustomobject]@{ id = $Id; gate = $Name; status = $status; seconds = $secs; detail = $detail; tail = $tail })
    $color = if ($status -eq "PASS") { "Green" } else { "Red" }
    Write-Host ("{0,-5} {1} {2} ({3}s) {4}" -f $status, $Id, $Name, $secs, $detail) -ForegroundColor $color
}

function Assert-Exit([string]$What) { if ($LASTEXITCODE -ne 0) { throw "$What exited $LASTEXITCODE" } }

function Invoke-Psql([string]$Sql) {
    $r = docker exec $PgContainer psql -U flowforge -d flowforge -At -v ON_ERROR_STOP=1 -c $Sql
    Assert-Exit "psql"
    return (($r | Out-String).Trim())
}

$HostDbEnv = @{ DATABASE_URL = $AppUrlOnHost; FLOWFORGE_DATABASE_URL = $AppUrlOnHost; FLOWFORGE_ENV = "test" }
function Use-HostDbEnv([scriptblock]$Body) {
    $saved = @{}
    foreach ($k in $HostDbEnv.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k, "Process"); [Environment]::SetEnvironmentVariable($k, $HostDbEnv[$k], "Process") }
    try { & $Body } finally { foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k], "Process") } }
}

try {
    # ---------------------------------------------------------------- database
    Invoke-Gate "G01" "Migration rehearsal (disposable DB: upgrade, downgrade -1, re-upgrade, RLS)" {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\acceptance\Invoke-MigrationRehearsal.ps1" -ProjectRoot $Root
    }

    Invoke-Gate "G02" "Fresh database: alembic upgrade head" {
        $before = Invoke-Psql "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema') AND table_type='BASE TABLE';"
        "tables_before=$before"
        & $Python -m alembic upgrade head; Assert-Exit "alembic upgrade head"
        "alembic_version=" + (Invoke-Psql "SELECT string_agg(version_num, ',') FROM alembic_version;")
        "public_tables=" + (Invoke-Psql "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
    }

    Invoke-Gate "G03" "Alembic single head and no autogenerate drift" {
        & $Python -m alembic heads; Assert-Exit "alembic heads"
        & $Python -m alembic check; Assert-Exit "alembic check"
    }

    Invoke-Gate "G04" "RLS coverage on every tenant table + restricted runtime role" {
        $q = "WITH t AS (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id') SELECT count(*) FROM t JOIN pg_class c ON c.relname=t.table_name JOIN pg_namespace n ON n.oid=c.relnamespace AND n.nspname='public' LEFT JOIN (SELECT tablename,count(*) p FROM pg_policies WHERE schemaname='public' GROUP BY tablename) p ON p.tablename=t.table_name WHERE NOT c.relrowsecurity OR NOT c.relforcerowsecurity OR coalesce(p.p,0)=0;"
        $failures = Invoke-Psql $q
        "tenant_tables=" + (Invoke-Psql "SELECT count(DISTINCT table_name) FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id';")
        "policies=" + (Invoke-Psql "SELECT count(*) FROM pg_policies;")
        "rls_failures=$failures"
        $role = Invoke-Psql "SELECT concat_ws('|',rolsuper,rolbypassrls,rolcanlogin) FROM pg_roles WHERE rolname='flowforge_app';"
        "flowforge_app super|bypassrls|login=$role"
        if ($failures -ne "0") { throw "$failures tenant tables lack forced RLS or a policy" }
        if ($role -notin @("f|f|t","false|false|true")) { throw "flowforge_app is not a restricted login role" }
    }

    # ---------------------------------------------------------------- isolated API
    Invoke-Gate "G05" "Start isolated API container as flowforge_app" {
        docker rm -f $ApiContainer 2>$null | Out-Null
        $global:LASTEXITCODE = 0
        $jwt = -join ((48..57) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
        docker run -d --name $ApiContainer --network flowforge-phase1_default -p "${IsolatedApiPort}:8000" `
            -e "DATABASE_URL=$AppUrlInDocker" -e "FLOWFORGE_DATABASE_URL=$AppUrlInDocker" `
            -e "FLOWFORGE_ENV=test" -e "FLOWFORGE_JWT_SECRET=$jwt" flowforge-phase1-api | Out-Null
        Assert-Exit "docker run"
        $ok = $false
        foreach ($i in 1..45) { try { $h = Invoke-RestMethod "$Api/api/v1/health" -TimeoutSec 3; if ($h.status -eq "ok") { $ok = $true; break } } catch {}; Start-Sleep 2 }
        if (-not $ok) { docker logs --tail 60 $ApiContainer; throw "isolated API did not become healthy" }
        "isolated_api=$Api healthy"
    }

    Invoke-Gate "G06" "Runtime DB role probe (expects flowforge_app|row_security on|not superuser)" {
        $p = "import asyncio`nfrom sqlalchemy import text`nfrom flowforge.db.session import engine`nasync def main():`n    async with engine.connect() as c:`n        print('|'.join((await c.execute(text(""select current_user,current_setting('row_security'),current_setting('is_superuser')""))).one()))`n    await engine.dispose()`nasyncio.run(main())`n"
        $o = @($p | docker exec -i $ApiContainer python -)
        Assert-Exit "probe"
        $o
        if ($o[-1].Trim() -ne "flowforge_app|on|off") { throw "unsafe runtime: $($o[-1])" }
    }

    Invoke-Gate "G07" "Health contract (/api/v1/health ok, /phase1b/health ready+database+storage)" {
        $h = Invoke-RestMethod "$Api/api/v1/health" -TimeoutSec 15
        $r = Invoke-RestMethod "$Api/phase1b/health" -TimeoutSec 15
        ($h | ConvertTo-Json -Compress); ($r | ConvertTo-Json -Compress)
        if ($h.status -ne "ok" -or $r.status -ne "ready" -or -not $r.database -or -not $r.storage) { throw "health contract failed" }
    }

    Invoke-Gate "G08" "Invoke-FlowForgeAcceptance.ps1 as written (-SkipE2E, isolated API)" {
        $env:FLOWFORGE_ENV = "test"
        $env:FLOWFORGE_TEST_PASSWORD = "Acc-" + [guid]::NewGuid().ToString("N")
        try {
            Use-HostDbEnv { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\acceptance\Invoke-FlowForgeAcceptance.ps1" -Api $Api -PostgresContainer $PgContainer -SkipE2E }
        } finally { Remove-Item Env:\FLOWFORGE_TEST_PASSWORD -ErrorAction SilentlyContinue; Remove-Item Env:\FLOWFORGE_ENV -ErrorAction SilentlyContinue }
    }

    # ---------------------------------------------------------------- code quality (each independently)
    Invoke-Gate "G09" "Python compileall" { & $Python -m compileall -q ".\src" }
    Invoke-Gate "G10" "Ruff check (src, tests, migrations)" { & $Python -m ruff check ".\src" ".\tests" ".\migrations" --statistics }
    Invoke-Gate "G11" "Ruff format --check" { & $Python -m ruff format --check ".\src" ".\tests" ".\migrations" }
    Invoke-Gate "G12" "MyPy (src\flowforge)" { & $Python -m mypy --no-incremental ".\src\flowforge" }
    Invoke-Gate "G13" "OpenAPI import (>= 358 paths)" { & $Python -c "from flowforge.main import app; p=app.openapi()['paths']; print(f'openapi_paths={len(p)}'); assert len(p)>=358" }

    Invoke-Gate "G14" "Backend test suite (pytest, fresh DB as flowforge_app)" {
        Use-HostDbEnv { & $Python -m pytest -q -p no:cacheprovider ".\tests" -rfE --maxfail=10000 --junitxml (Join-Path $Out "pytest.xml") }
    }

    # ---------------------------------------------------------------- tenancy
    Invoke-Gate "G15" "API tenant-isolation tests" {
        $tests = @(".\tests\phase1\acceptance\test_tenant_isolation_matrix.py", ".\tests\security_hardening\test_security.py", ".\tests\test_security.py") | Where-Object { Test-Path $_ }
        "tests=" + ($tests -join ",")
        if (-not $tests) { throw "no tenant-security tests found" }
        Use-HostDbEnv { & $Python -m pytest -q -p no:cacheprovider @tests }
    }
    Invoke-Gate "G16" "Four-tenant PostgreSQL RLS matrix" {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\acceptance\Invoke-FourTenantRls.ps1" -RuntimePassword $RuntimePassword
    }

    # ---------------------------------------------------------------- operations
    Invoke-Gate "G17" "Backup and restore rehearsal" {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\acceptance\Invoke-BackupRestore.ps1" -ProjectRoot $Root
    }
    Invoke-Gate "G18" "Controlled failure recovery (rollback probe + isolated API restart)" {
        $sql = "BEGIN; CREATE TEMP TABLE rollback_probe(v int); INSERT INTO rollback_probe VALUES (1); ROLLBACK; SELECT to_regclass('pg_temp.rollback_probe') IS NULL;"
        $r = @($sql | docker exec -i $PgContainer psql -q -U flowforge -d flowforge -At -v ON_ERROR_STOP=1); Assert-Exit "rollback probe"
        "rollback_probe=" + ($r | Where-Object { $_ } | Select-Object -Last 1)
        if ((($r | Where-Object { $_ } | Select-Object -Last 1)).Trim() -ne "t") { throw "rollback probe failed" }
        docker restart $ApiContainer | Out-Null; Assert-Exit "docker restart"
        $ok = $false
        foreach ($i in 1..60) { try { if ((Invoke-RestMethod "$Api/api/v1/health" -TimeoutSec 3).status -eq "ok") { $ok = $true; break } } catch {}; Start-Sleep 2 }
        if (-not $ok) { throw "isolated API did not recover after restart" }
        "recovered=true"
    }
    Invoke-Gate "G19" "Phase 4 comprehensive live test (host uvicorn :$Phase4Port as flowforge_app)" {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\Run-Phase4-Comprehensive-Live-Test.ps1" -RuntimePassword $RuntimePassword -Port $Phase4Port
    }

    # ---------------------------------------------------------------- frontend
    Push-Location (Join-Path $Root "web")
    try {
        Invoke-Gate "G20" "Frontend typecheck" { & npm.cmd run typecheck }
        Invoke-Gate "G21" "Frontend lint" { & npm.cmd run lint }
        Invoke-Gate "G22" "Frontend unit tests (vitest)" { & npm.cmd test }
        Invoke-Gate "G23" "Frontend production build" { & npm.cmd run build }
    } finally { Pop-Location }

    # ---------------------------------------------------------------- security
    Invoke-Gate "G24" "Tracked secret scan" {
        $all = @(git grep -n -I -E '(sk_live_|ghp_|github_pat_|BEGIN (RSA |OPENSSH )?PRIVATE KEY-----|://[A-Za-z0-9_]+:[^@$/{ ]{6,}@)' -- . ':!*.example' ':!scripts/Package-FlowForge-For-Complete-Build.ps1' ':!docs/*' ':!scripts/acceptance/Invoke-PhaseBBackend.ps1' ':!scripts/acceptance/Invoke-IsolatedAcceptanceRerun.ps1' 2>$null)
        $code = $LASTEXITCODE
        if ($code -gt 1) { throw "git grep failed ($code)" }
        # The local-only development default (flowforge:flowforge@localhost) is reported, not counted as a leak.
        $devDefaults = @($all | Where-Object { $_ -match '://flowforge:flowforge@localhost' })
        $bad = @($all | Where-Object { $_ -notmatch '://flowforge:flowforge@localhost' })
        "dev_default_credentials_in_tracked_files=$($devDefaults.Count)"
        $devDefaults | ForEach-Object { "  dev-default: " + ($_ -split ':')[0] }
        "hits=$($bad.Count)"
        $bad | ForEach-Object { ($_ -replace '(://[^:]+:)[^@]+@', '$1<redacted>@') }
        if ($bad.Count -gt 0) { throw "potential tracked secrets: $($bad.Count)" }
        $global:LASTEXITCODE = 0
    }
}
finally {
    if (-not $KeepIsolatedApi) { docker rm -f $ApiContainer 2>$null | Out-Null }
    $RuntimePassword = $null
    $Results | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Out "results.json") -Encoding UTF8
    $lines = @("FLOWFORGE ISOLATED ACCEPTANCE RERUN", "RUN=$Stamp", "COMMIT=$((git rev-parse HEAD).Trim())", "DATABASE=$PgContainer/flowforge (isolated)", "API=$Api (isolated, flowforge_app)", "")
    foreach ($r in $Results) { $lines += ("{0,-4} {1} {2} ({3}s) {4}" -f $r.status, $r.id, $r.gate, $r.seconds, $r.detail) }
    $lines += ""
    $lines += "PASS=$(@($Results | Where-Object status -eq 'PASS').Count) FAIL=$(@($Results | Where-Object status -eq 'FAIL').Count) TOTAL=$($Results.Count)"
    $lines += "NOT_RUN=Playwright e2e (playwright.config reuses :3000, which is the live web/API)"
    $lines | Set-Content (Join-Path $Out "summary.txt") -Encoding UTF8
    Write-Host ""
    $lines | ForEach-Object { Write-Host $_ }
}

<#
.SYNOPSIS  Rehearse the production cutover on a disposable copy of the production stack.
.DESCRIPTION
    Project "flowforge-rehearsal" on web :3300, api :8300, db 127.0.0.1:5436, with its own
    volumes. Runs build, migrations, import (and an idempotent re-import), stack
    verification, the release workflow tests and signed-in browser tests against it,
    backup + restore, API restart, and stop/start persistence. Removes ONLY the
    rehearsal project's containers and volumes at the end (-KeepStack to keep them).
    The live system and the recovered database are only read (import source).
    -FromProductionBackup: instead of importing from the recovered database, restore a fresh
    verified backup of the live production database and upgrade it with the new migrations
    (the update path), then run the same verification and tests.
#>
[CmdletBinding()]
param([switch]$KeepStack, [switch]$FromProductionBackup)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
$root = Get-FFRoot
$project = "flowforge-rehearsal"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $root "var\rehearsal\$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$log = Join-Path $out "rehearsal.log"
$results = New-Object System.Collections.Generic.List[object]
$envFile = Join-Path $root ".env.production"
$python = Join-Path $root ".venv\Scripts\python.exe"

function Step([string]$Id, [string]$Name, [scriptblock]$Body) {
    Write-FFLog "RUNNING $Id $Name" $log
    $file = Join-Path $out "$Id.log"
    $start = Get-Date
    try {
        # Native tools (docker, npx) write normal progress to stderr; judge steps by
        # explicit throws and exit codes, not by stderr (PowerShell 5.1 behaviour).
        $ErrorActionPreference = "Continue"
        & $Body *>&1 | ForEach-Object { "$_" } | Out-File -FilePath $file -Encoding utf8
        $ErrorActionPreference = "Stop"
        $status = "PASS"; $detail = ""
    } catch {
        $ErrorActionPreference = "Stop"
        $status = "FAIL"; $detail = $_.Exception.Message
        Add-Content -Path $file -Value "EXCEPTION: $detail" -Encoding utf8
    }
    $results.Add([pscustomobject]@{ id = $Id; step = $Name; status = $status; seconds = [math]::Round(((Get-Date) - $start).TotalSeconds, 1); detail = $detail })
    Write-FFLog ("{0} {1} {2} {3}" -f $status, $Id, $Name, $detail) $log
    if ($status -eq "FAIL" -and $Id -lt "R06") { throw "Rehearsal aborted at ${Id}: $detail" }
}

$env:FF_WEB_PORT = "3300"; $env:FF_API_PORT = "8300"; $env:FF_DB_PORT = "5436"
# Never start the public tunnel for a rehearsal (it would share live traffic): the shell
# values override COMPOSE_PROFILES / FLOWFORGE_TUNNEL_TOKEN from .env.production.
$env:COMPOSE_PROFILES = "rehearsal-no-tunnel"; $env:FLOWFORGE_TUNNEL_TOKEN = ""
try {
    Step "R00" "Script syntax" {
        foreach ($f in Get-ChildItem $PSScriptRoot -Filter *.ps1) {
            $errs = $null; [void][Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$null, [ref]$errs)
            if ($errs.Count) { throw "$($f.Name): $($errs[0].Message)" }
        }
        & $python -I -m py_compile (Join-Path $PSScriptRoot "import_production_data.py"); if ($LASTEXITCODE) { throw "import script does not compile" }
        "ok"
    }
    Step "R01" "Secrets file (generated if missing)" { & (Join-Path $PSScriptRoot "Install-FlowForge.ps1") }
    Step "R02" "Build images" { Invoke-FFCompose -Project $project -Arguments @("build") -Description "build" }
    if ($FromProductionBackup) {
        Step "R03" "Restore live production backup, then upgrade with new migrations" {
            $source = & (Join-Path $PSScriptRoot "Backup-FlowForge.ps1") -Project "flowforge" -Label "rehearsal-source" | Select-Object -Last 1
            $before = (docker exec (Get-FFContainer "flowforge" "db") psql -U flowforge_owner -d flowforge -Atc "SELECT version_num FROM alembic_version").Trim()
            Invoke-FFCompose -Project $project -Arguments @("up", "-d", "--wait", "db") -Description "db up"
            $db = Get-FFContainer $project "db"
            Invoke-FFNative -Description "copy backup" -Command { docker cp $source "${db}:/tmp/source.dump" } | Out-Null
            Invoke-FFNative -Description "pg_restore" -Command { docker exec $db pg_restore -U flowforge_owner -d flowforge --no-owner --exit-on-error /tmp/source.dump } | Out-Null
            docker exec $db rm -f /tmp/source.dump | Out-Null
            Invoke-FFCompose -Project $project -Arguments @("run", "--rm", "migrate") -Description "migrate (upgrade)"
            $after = (docker exec $db psql -U flowforge_owner -d flowforge -Atc "SELECT version_num FROM alembic_version").Trim()
            "restored production at $before; upgraded to $after"
        }
        Step "R04" "Production data present after upgrade" {
            $db = Get-FFContainer $project "db"
            $n = (docker exec $db psql -U flowforge_owner -d flowforge -Atc "SELECT count(*) FROM tenants WHERE slug = 'flowforge-production'").Trim()
            if ($n -ne "1") { throw "production tenant missing after restore" }
            "production tenant present"
        }
    } else {
        Step "R03" "Database + migrations from blank" {
            Invoke-FFCompose -Project $project -Arguments @("up", "-d", "db") -Description "db up"
            Invoke-FFCompose -Project $project -Arguments @("run", "--rm", "migrate") -Description "migrate"
        }
        Step "R04" "Import tenant, users and reference data" { & (Join-Path $PSScriptRoot "Import-FlowForgeData.ps1") -TargetPort 5436 }
    }
    Step "R05" "Start api, web and services" {
        Invoke-FFCompose -Project $project -Arguments @("up", "-d") -Description "up"
        Wait-FFHttp "http://127.0.0.1:8300/api/v1/health" 240
        Wait-FFHttp "http://127.0.0.1:3300/login" 240
    }
    Step "R06" "Stack verification" { & (Join-Path $PSScriptRoot "Test-FlowForgeStack.ps1") -Project $project -ApiPort 8300 -WebPort 3300 -ReportPath (Join-Path $out "verification.json") }
    if (-not $FromProductionBackup) {
    Step "R07" "Import is idempotent (re-run inserts nothing)" {
        $report = (& (Join-Path $PSScriptRoot "Import-FlowForgeData.ps1") -TargetPort 5436 | Out-String)
        $json = $report.Substring($report.IndexOf("{"), $report.LastIndexOf("}") - $report.IndexOf("{") + 1) | ConvertFrom-Json
        $sum = ($json.inserted_this_run.PSObject.Properties | Measure-Object -Property Value -Sum).Sum
        if ($sum -ne 0) { throw "re-import inserted $sum rows" }
        "re-import inserted 0 rows; reconciled=$($json.reconciled)"
    }
    }
    Step "R08" "Release workflow tests against the rehearsal database" {
        $cfg = Read-FFEnvFile $envFile
        $env:FLOWFORGE_DATABASE_URL = "postgresql+asyncpg://flowforge_app:$($cfg['FLOWFORGE_APP_DB_PASSWORD'])@127.0.0.1:5436/flowforge"
        try { & $python -m pytest -q -p no:cacheprovider (Join-Path $root "tests\workflows") (Join-Path $root "tests\rls"); if ($LASTEXITCODE) { throw "workflow tests failed" } }
        finally { Remove-Item Env:\FLOWFORGE_DATABASE_URL -ErrorAction SilentlyContinue }
    }
    Step "R09" "Signed-in browser tests against the rehearsal API" {
        Push-Location (Join-Path $root "web")
        $env:E2E_API_BASE_URL = "http://127.0.0.1:8300"
        try { & npx.cmd playwright test --reporter=line; if ($LASTEXITCODE) { throw "browser tests failed" } }
        finally { Remove-Item Env:\E2E_API_BASE_URL -ErrorAction SilentlyContinue; Pop-Location }
    }
    Step "R10" "Backup and restore round trip" {
        $backup = & (Join-Path $PSScriptRoot "Backup-FlowForge.ps1") -Project $project -Label "rehearsal" | Select-Object -Last 1
        $db = Get-FFContainer $project "db"
        docker cp $backup "${db}:/tmp/restore.dump" | Out-Null
        Invoke-FFNative -Description "createdb" -Command { docker exec $db createdb -U flowforge_owner restore_check }
        try {
            Invoke-FFNative -Description "pg_restore" -Command { docker exec $db pg_restore -U flowforge_owner -d restore_check --no-owner /tmp/restore.dump }
            $q = "SELECT (SELECT count(*) FROM information_schema.tables WHERE table_schema='public')||'/'||(SELECT count(*) FROM tenants)||'/'||(SELECT count(*) FROM tax_jurisdictions)||'/'||(SELECT version_num FROM alembic_version)"
            $a = (docker exec $db psql -U flowforge_owner -d flowforge -Atc $q).Trim()
            $b = (docker exec $db psql -U flowforge_owner -d restore_check -Atc $q).Trim()
            if ($a -ne $b) { throw "restore mismatch source=$a restored=$b" }
            "tables/tenants/jurisdictions/revision identical: $a"
        } finally {
            docker exec $db dropdb -U flowforge_owner --if-exists restore_check | Out-Null
            docker exec $db rm -f /tmp/restore.dump | Out-Null
        }
    }
    Step "R11" "API restart recovery" {
        Invoke-FFCompose -Project $project -Arguments @("restart", "api") -Description "restart api"
        Wait-FFHttp "http://127.0.0.1:8300/api/v1/health" 120
        "recovered"
    }
    Step "R12" "Stop/start keeps data" {
        $db = Get-FFContainer $project "db"
        $before = (docker exec $db psql -U flowforge_owner -d flowforge -Atc "SELECT count(*) FROM users").Trim()
        & (Join-Path $PSScriptRoot "Stop-FlowForge.ps1") -Project $project
        & (Join-Path $PSScriptRoot "Start-FlowForge.ps1") -Project $project
        $db = Get-FFContainer $project "db"
        $after = (docker exec $db psql -U flowforge_owner -d flowforge -Atc "SELECT count(*) FROM users").Trim()
        if ($before -ne $after) { throw "users before=$before after=$after" }
        & (Join-Path $PSScriptRoot "Test-FlowForgeStack.ps1") -Project $project -ApiPort 8300 -WebPort 3300
    }
} finally {
    if (-not $KeepStack) {
        try { Invoke-FFCompose -Project $project -Arguments @("down", "-v", "--remove-orphans") -Description "remove rehearsal stack" | Out-Null } catch { Write-Warning $_.Exception.Message }
    }
    Remove-Item Env:\FF_WEB_PORT, Env:\FF_API_PORT, Env:\FF_DB_PORT, Env:\COMPOSE_PROFILES, Env:\FLOWFORGE_TUNNEL_TOKEN -ErrorAction SilentlyContinue
    $results | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $out "results.json") -Encoding UTF8
    $summary = @("FLOWFORGE CUTOVER REHEARSAL $stamp", "") + ($results | ForEach-Object { "{0} {1} {2} ({3}s) {4}" -f $_.status, $_.id, $_.step, $_.seconds, $_.detail })
    $failed = @($results | Where-Object status -eq "FAIL").Count
    $summary += "", "PASS=$(@($results | Where-Object status -eq 'PASS').Count) FAIL=$failed"
    $summary | Set-Content (Join-Path $out "summary.txt") -Encoding UTF8
    $summary | ForEach-Object { Write-Host $_ }
}
if (@($results | Where-Object status -eq "FAIL").Count -gt 0) { throw "REHEARSAL FAILED" }
Write-Host "REHEARSAL PASSED" -ForegroundColor Green

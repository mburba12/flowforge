<#
.SYNOPSIS  Cut the live system over from the recovered runtime to the production stack.
.DESCRIPTION
    1. Back up the recovered database (verified).
    2. Build the production images.
    3. Start the production database and run migrations (owner role).
    4. Import the approved tenant, users and reference data (reconciled).
    5. Stop the old live API and web containers (kept, restart disabled).
    6. Start the production API and web on the live ports; verify (Test-FlowForgeStack).
       Any failure from step 5 on triggers an automatic rollback to the old runtime.
    7. Stop the recovered database container (kept intact, restart disabled) and
       back up the new production database.
    Writes var\cutover\<timestamp>\ (log, verification report, record.json).
#>
[CmdletBinding()]
param(
    [string]$OldApi = "flowforge-phase1-api-1",
    [string]$OldWeb = "flowforge-phase1-web-1",
    [string]$OldDb = "forgeflow-v4-phase0-postgres-1"
)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
$root = Get-FFRoot
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $root "var\cutover\$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$log = Join-Path $out "cutover.log"
$envFile = Join-Path $root ".env.production"
$cfg = Read-FFEnvFile $envFile
$record = [ordered]@{ started = (Get-Date).ToString("o"); commit = (git -C $root rev-parse --short HEAD).Trim() }

Write-FFLog "CUTOVER START $stamp" $log
foreach ($c in $OldApi, $OldWeb, $OldDb) {
    if (-not (docker ps -q --filter "name=^$c$")) { throw "Precondition failed: $c is not running." }
}

# 1. Backup of the recovered database.
$backupDir = Join-Path $root "var\backups"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$tmp = "/tmp/forgeflow-precutover-$stamp.dump"
$oldBackup = Join-Path $backupDir "forgeflow-precutover-$stamp.dump"
Invoke-FFNative -Description "Backup recovered database" -Command { docker exec $OldDb pg_dump -U forgeflow -d forgeflow -Fc -f $tmp } | Out-Null
Invoke-FFNative -Description "Copy recovered backup" -Command { docker cp "${OldDb}:$tmp" $oldBackup } | Out-Null
$entries = Invoke-FFNative -Description "Verify recovered backup" -Command { docker exec $OldDb sh -c "pg_restore -l $tmp | grep -c 'TABLE DATA'" }
docker exec $OldDb rm -f $tmp | Out-Null
if ([int]($entries | Select-Object -Last 1) -le 0) { throw "Recovered database backup is empty." }
$record.recovered_backup = $oldBackup
Write-FFLog "1 BACKUP OK $oldBackup ($($entries | Select-Object -Last 1) table-data entries)" $log

# 2-3. Build, database, migrations.
Invoke-FFCompose -Arguments @("build") -Description "Build production images" | Out-Null
Write-FFLog "2 BUILD OK" $log
Invoke-FFCompose -Arguments @("up", "-d", "db") -Description "Start production database" | Out-Null
Invoke-FFCompose -Arguments @("run", "--rm", "migrate") -Description "Run migrations" | Out-Null
$rev = Invoke-FFNative -Description "Read revision" -Command { docker exec (Get-FFContainer "flowforge" "db") psql -U flowforge_owner -d flowforge -Atc "SELECT version_num FROM alembic_version" }
$record.revision = ($rev -join "").Trim()
Write-FFLog "3 MIGRATIONS OK revision=$($record.revision)" $log

# 4. Import.
& (Join-Path $PSScriptRoot "Import-FlowForgeData.ps1") *>&1 | Tee-Object -FilePath (Join-Path $out "import.log") | Out-Null
if (-not (Select-String -Path (Join-Path $out "import.log") -Pattern '"reconciled": true' -Quiet)) { throw "Import did not reconcile; old runtime still live. See import.log." }
Write-FFLog "4 IMPORT RECONCILED" $log

# 5-6. Switch, verify, roll back automatically on failure.
$switched = $false
try {
    docker update --restart=no $OldApi $OldWeb | Out-Null
    docker stop $OldApi $OldWeb | Out-Null
    $switched = $true
    Write-FFLog "5 OLD API/WEB STOPPED" $log
    Invoke-FFCompose -Arguments @("up", "-d") -Description "Start production stack" | Out-Null
    Wait-FFHttp "http://127.0.0.1:$($cfg['FF_API_PORT'])/api/v1/health" 240
    Wait-FFHttp "http://127.0.0.1:$($cfg['FF_WEB_PORT'])/login" 240
    & (Join-Path $PSScriptRoot "Test-FlowForgeStack.ps1") -ApiPort ([int]$cfg["FF_API_PORT"]) -WebPort ([int]$cfg["FF_WEB_PORT"]) -ReportPath (Join-Path $out "verification.json")
    Write-FFLog "6 PRODUCTION STACK VERIFIED" $log
} catch {
    Write-FFLog "FAILURE: $($_.Exception.Message) - rolling back" $log
    if ($switched) { & (Join-Path $PSScriptRoot "Rollback-FlowForgeCutover.ps1") -OldApi $OldApi -OldWeb $OldWeb -OldDb $OldDb *>&1 | Tee-Object -FilePath (Join-Path $out "rollback.log") | Out-Null }
    $record.result = "ROLLED_BACK"; $record | ConvertTo-Json | Set-Content (Join-Path $out "record.json") -Encoding UTF8
    throw
}

# 7. Retire the recovered database container (intact), back up the new database.
docker update --restart=no $OldDb | Out-Null
docker stop $OldDb | Out-Null
Write-FFLog "7 RECOVERED DATABASE CONTAINER STOPPED (volume intact, restart disabled)" $log
$record.production_backup = (& (Join-Path $PSScriptRoot "Backup-FlowForge.ps1") -Label "postcutover" | Select-Object -Last 1)
$record.result = "LIVE_ON_PRODUCTION_STACK"
$record.finished = (Get-Date).ToString("o")
$record | ConvertTo-Json | Set-Content (Join-Path $out "record.json") -Encoding UTF8
Write-FFLog "CUTOVER COMPLETE" $log
Write-Host "FLOWFORGE CUTOVER COMPLETE ($out)" -ForegroundColor Green

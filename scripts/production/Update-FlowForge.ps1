<#
.SYNOPSIS  Deploy the current code to the running production stack, with automatic image rollback.
.DESCRIPTION
    1. Verified database backup (Backup-FlowForge.ps1 -Label preupdate).
    2. Tag the images currently in use as rollback images.
    3. Rebuild and restart (the migrate service applies new migrations before the API starts).
    4. Verify (Test-FlowForgeStack.ps1). On failure the previous images are restored and the
       stack restarted. Migrations in this project are additive, so previous code runs on the
       migrated schema; restore the pre-update backup only if a migration itself is at fault.
    Writes var\updates\<timestamp>\.
#>
[CmdletBinding()]
param([string]$Project = "flowforge")
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
$root = Get-FFRoot
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $root "var\updates\$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$log = Join-Path $out "update.log"
$cfg = Read-FFEnvFile (Join-Path $root ".env.production")

Write-FFLog "UPDATE START $stamp commit=$((git -C $root rev-parse --short HEAD).Trim())" $log
$backup = & (Join-Path $PSScriptRoot "Backup-FlowForge.ps1") -Project $Project -Label "preupdate" | Select-Object -Last 1
Write-FFLog "1 BACKUP $backup" $log

$images = @("flowforge-api:local", "flowforge-web:local")
foreach ($image in $images) {
    $rollback = $image -replace ":local$", ":rollback-$stamp"
    Invoke-FFNative -Description "Tag $image" -Command { docker tag $image $rollback } | Out-Null
}
Write-FFLog "2 ROLLBACK IMAGES TAGGED rollback-$stamp" $log

try {
    Invoke-FFCompose -Project $Project -Arguments @("build") -Description "Build" | Out-Null
    # The API now runs as an unprivileged account (uid 10001): give it its data volume.
    Invoke-FFCompose -Project $Project -Arguments @("run", "--rm", "--no-deps", "--user", "0", "--entrypoint", "chown", "api", "-R", "10001:10001", "/data") -Description "Volume ownership" | Out-Null
    Invoke-FFCompose -Project $Project -Arguments @("up", "-d") -Description "Up" | Out-Null
    Wait-FFHttp "http://127.0.0.1:$($cfg['FF_API_PORT'])/api/v1/health" 240
    Wait-FFHttp "http://127.0.0.1:$($cfg['FF_WEB_PORT'])/login" 240
    Write-FFLog "3 REBUILT AND RESTARTED" $log
    & (Join-Path $PSScriptRoot "Test-FlowForgeStack.ps1") -Project $Project -ApiPort ([int]$cfg["FF_API_PORT"]) -WebPort ([int]$cfg["FF_WEB_PORT"]) -ReportPath (Join-Path $out "verification.json")
    Write-FFLog "4 VERIFIED" $log
} catch {
    Write-FFLog "FAILURE: $($_.Exception.Message) - restoring previous images" $log
    foreach ($image in $images) {
        $rollback = $image -replace ":local$", ":rollback-$stamp"
        docker tag $rollback $image | Out-Null
    }
    Invoke-FFCompose -Project $Project -Arguments @("up", "-d", "--no-build", "--force-recreate", "api", "web") -Description "Restore previous images" | Out-Null
    Write-FFLog "ROLLED BACK to rollback-$stamp images (database backup: $backup)" $log
    throw
}
Write-FFLog "UPDATE COMPLETE" $log
Write-Host "FLOWFORGE UPDATED ($out)" -ForegroundColor Green

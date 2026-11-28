<#
.SYNOPSIS  Return the live system to the recovered runtime (pre-cutover state).
.DESCRIPTION
    Stops the production API and web (the production database and its volume are
    kept), restarts the recovered database, API and web containers and restores
    their restart policy, then checks health. Nothing is deleted.
#>
[CmdletBinding()]
param(
    [string]$OldApi = "flowforge-phase1-api-1",
    [string]$OldWeb = "flowforge-phase1-web-1",
    [string]$OldDb = "forgeflow-v4-phase0-postgres-1"
)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
Write-Host "ROLLBACK: stopping production api/web"
try { Invoke-FFCompose -Arguments @("stop", "api", "web") -Description "Stop production api/web" | Out-Null } catch { Write-Warning $_.Exception.Message }
foreach ($c in $OldDb, $OldApi, $OldWeb) {
    docker update --restart=unless-stopped $c | Out-Null
    Invoke-FFNative -Description "Start $c" -Command { docker start $c } | Out-Null
}
Wait-FFHttp "http://127.0.0.1:8000/api/v1/health" 180
Wait-FFHttp "http://127.0.0.1:3000/login" 180
Write-Host "ROLLBACK COMPLETE: recovered runtime is live on :3000 / :8000" -ForegroundColor Yellow

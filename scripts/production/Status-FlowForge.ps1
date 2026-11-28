<#
.SYNOPSIS  Show service state, health endpoints and the database migration revision.
#>
[CmdletBinding()]
param([string]$Project = "flowforge", [string]$EnvFile)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
if (-not $EnvFile) { $EnvFile = Join-Path (Get-FFRoot) ".env.production" }
$cfg = Read-FFEnvFile $EnvFile
Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments @("ps", "--format", "table {{.Service}}\t{{.State}}\t{{.Health}}\t{{.Ports}}") -Description "Status"
foreach ($check in @(
        @{ Name = "API health"; Url = "http://127.0.0.1:$($cfg['FF_API_PORT'])/api/v1/health" },
        @{ Name = "Web sign-in"; Url = "http://127.0.0.1:$($cfg['FF_WEB_PORT'])/login" },
        @{ Name = "Web -> API proxy"; Url = "http://127.0.0.1:$($cfg['FF_WEB_PORT'])/api/flowforge/api/v1/health" })) {
    try { $code = (Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 10).StatusCode } catch { $code = "DOWN" }
    "{0,-18} {1}" -f $check.Name, $code
}
$db = Get-FFContainer $Project "db"
$rev = Invoke-FFNative -Description "Read migration revision" -Command { docker exec $db psql -U flowforge_owner -d flowforge -Atc "SELECT version_num FROM alembic_version" }
"Migration revision  $($rev -join ',')"

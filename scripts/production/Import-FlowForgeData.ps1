<#
.SYNOPSIS  Import the approved tenant, users and reference data from the recovered database.
.DESCRIPTION
    Source: the recovered forgeflow database (read-only session), credentials from
    .env.recovered-database. Target: the production stack's database as its owner,
    credentials from .env.production. Idempotent; prints the reconciliation report
    and fails unless every count reconciles. See import_production_data.py for scope.
#>
[CmdletBinding()]
param(
    [string]$EnvFile,
    [int]$TargetPort = 0,
    [string]$SourceEnvFile,
    [int]$SourcePort = 5432,
    [string]$TenantSlug = "flowforge-production"
)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
$root = Get-FFRoot
if (-not $EnvFile) { $EnvFile = Join-Path $root ".env.production" }
if (-not $SourceEnvFile) { $SourceEnvFile = Join-Path $root ".env.recovered-database" }
$cfg = Read-FFEnvFile $EnvFile
$src = Read-FFEnvFile $SourceEnvFile
if ($TargetPort -eq 0) { $TargetPort = [int]$(if ($env:FF_DB_PORT) { $env:FF_DB_PORT } else { $cfg["FF_DB_PORT"] }) }

$python = Join-Path $root ".venv\Scripts\python.exe"
$env:IMPORT_SOURCE_DSN = ConvertTo-FFLibpqDsn $src["FLOWFORGE_PROD_DATABASE_URL"] "127.0.0.1" $SourcePort
$env:IMPORT_TARGET_DSN = "postgresql://flowforge_owner:$($cfg['FLOWFORGE_DB_OWNER_PASSWORD'])@127.0.0.1:$TargetPort/flowforge"
$env:IMPORT_TENANT_SLUG = $TenantSlug
try {
    $script = Join-Path $PSScriptRoot "import_production_data.py"
    # Merge stderr so a Python traceback is shown in full; PowerShell 5.1 would
    # otherwise turn its first stderr line into a terminating error.
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $python -I $script 2>&1 | ForEach-Object { "$_" }; $code = $LASTEXITCODE }
    finally { $ErrorActionPreference = $previous }
    if ($code -ne 0) { throw "Import did not reconcile (exit $code)." }
} finally {
    Remove-Item Env:\IMPORT_SOURCE_DSN, Env:\IMPORT_TARGET_DSN, Env:\IMPORT_TENANT_SLUG -ErrorAction SilentlyContinue
}
Write-Host "IMPORT RECONCILED" -ForegroundColor Green

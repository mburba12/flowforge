[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RuntimePassword
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$SqlPath = Join-Path $PSScriptRoot "four-tenant-rls.sql"
$Sql = [System.IO.File]::ReadAllText($SqlPath)

$Sql |
    docker compose exec -T `
        -e PGPASSWORD="$RuntimePassword" `
        postgres `
        psql `
        -h 127.0.0.1 `
        -U flowforge_app `
        -d flowforge `
        -v ON_ERROR_STOP=1

if ($LASTEXITCODE -ne 0) {
    throw "Four-tenant RLS isolation matrix failed."
}

Write-Host "PASS: FOUR-TENANT RLS ISOLATION MATRIX" -ForegroundColor Green
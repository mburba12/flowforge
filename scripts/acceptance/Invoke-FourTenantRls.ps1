[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RuntimePassword
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$SetupPath = Join-Path $PSScriptRoot "four-tenant-setup.sql"
$MatrixPath = Join-Path $PSScriptRoot "four-tenant-rls.sql"
$CleanupPath = Join-Path $PSScriptRoot "four-tenant-cleanup.sql"

$SetupSql = [IO.File]::ReadAllText($SetupPath)
$MatrixSql = [IO.File]::ReadAllText($MatrixPath)
$CleanupSql = [IO.File]::ReadAllText($CleanupPath)

try {
    Write-Host "RUNNING: Four-tenant fixture setup" -ForegroundColor Cyan

    $SetupSql |
        docker compose exec -T postgres `
            psql `
            -U flowforge `
            -d flowforge `
            -v ON_ERROR_STOP=1

    if ($LASTEXITCODE -ne 0) {
        throw "Four-tenant fixture setup failed."
    }

    Write-Host "RUNNING: Four-tenant RLS matrix" -ForegroundColor Cyan

    $MatrixSql |
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
}
finally {
    Write-Host "RUNNING: Four-tenant fixture cleanup" -ForegroundColor Cyan

    $CleanupSql |
        docker compose exec -T postgres `
            psql `
            -U flowforge `
            -d flowforge `
            -v ON_ERROR_STOP=1

    if ($LASTEXITCODE -ne 0) {
        throw "Four-tenant fixture cleanup failed."
    }

    Write-Host "PASS: Four-tenant fixtures removed" -ForegroundColor Green
}

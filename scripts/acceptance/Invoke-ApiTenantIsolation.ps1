[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RuntimePassword,

    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,

    [string]$ApiBaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$RlsRunner = Join-Path $PSScriptRoot "Invoke-FourTenantRls.ps1"

Write-Host "RUNNING: API container check" -ForegroundColor Cyan
$ApiId = (docker compose ps --quiet api).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($ApiId)) { throw "API container is not running." }

Write-Host "RUNNING: Runtime database role check" -ForegroundColor Cyan
$Role = @(docker compose exec -T api python -c "from flowforge.core.config import settings; from sqlalchemy.engine import make_url; print(make_url(settings.database_url).username)")
if ($LASTEXITCODE -ne 0 -or $Role[-1].Trim() -ne "flowforge_app") { throw "API does not use flowforge_app." }

Write-Host "RUNNING: Live health endpoints" -ForegroundColor Cyan
$null = Invoke-RestMethod -Uri "$ApiBaseUrl/api/v1/health" -Method Get -TimeoutSec 30
$null = Invoke-RestMethod -Uri "$ApiBaseUrl/phase1b/health" -Method Get -TimeoutSec 30

Write-Host "RUNNING: API tenant-isolation tests" -ForegroundColor Cyan
$Tests = @(
    (Join-Path $ProjectRoot "tests\phase1\acceptance\test_tenant_isolation_matrix.py"),
    (Join-Path $ProjectRoot "tests\security_hardening\test_security.py"),
    (Join-Path $ProjectRoot "tests\test_security.py")
)
$ExistingTests = @($Tests | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
if ($ExistingTests.Count -eq 0) { throw "No tenant-security tests were found." }
& $Python -m pytest -q @ExistingTests
if ($LASTEXITCODE -ne 0) { throw "API tenant-securityiled." }

Write-Host "RUNNING: Four-tenant PostgreSQL RLS matrix" -ForegroundColor Cyan
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RlsRunner -RuntimePassword $RuntimePassword
if ($LASTEXITCODE -ne 0) { throw "Four-tenant RLS matrix failed." }

Write-Host "FLOWFORGE API TENANT-ISOLATION ACCEPTANCE PASSED" -ForegroundColor Green

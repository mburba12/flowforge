$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\Users\mackb\Downloads\Download the FlowForge Phase 1 scaffold\flowforge-phase1"
Set-Location $ProjectRoot
$Python = ".\.venv\Scripts\python.exe"
$Current = (& $Python -m alembic current) -join "`n"
$Heads = (& $Python -m alembic heads) -join "`n"
if ($Current -notmatch "ff_all_apis_delta_001") { throw "Wrong database revision" }
if ($Heads -notmatch "ff_all_apis_delta_001") { throw "Wrong Alembic head" }
& $Python .\scripts\Test-FlowForge-289-Table-Tenant-Isolation-V2.py
if ($LASTEXITCODE -ne 0) { throw "Tenant isolation failed" }
Push-Location .\web
try {
    npm run test:e2e
    if ($LASTEXITCODE -ne 0) { throw "Browser acceptance failed" }
} finally { Pop-Location }
Write-Host "FLOWFORGE UNIFIED ACCEPTANCE PASSED" -ForegroundColor Green

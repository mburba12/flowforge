param(
    [switch]$ApplyMigrations,
    [switch]$CreateCheckpoints
)
$ErrorActionPreference = "Stop"
$Python = ".\.venv\Scripts\python.exe"
$Waves = @("4d", "4e", "4f", "4g", "4h", "4i", "4j")
$Tags = @{
    "4d" = "v4.3.0-phase4d-unified-data"
    "4e" = "v4.4.0-phase4e-reconciliation"
    "4f" = "v4.5.0-phase4f-copilot-documents"
    "4g" = "v4.6.0-phase4g-governed-automation"
    "4h" = "v4.7.0-phase4h-enterprise-controls"
    "4i" = "v4.8.0-phase4i-production-connectors"
    "4j" = "v4.9.0-phase4j-release-candidate"
}
function Invoke-Gate([string]$Name, [scriptblock]$Action) {
    Write-Host "RUNNING: $Name" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
    Write-Host "PASSED: $Name" -ForegroundColor Green
}
foreach ($Wave in $Waves) {
    Write-Host "`n===== PHASE $($Wave.ToUpper()) =====" -ForegroundColor Yellow
    Invoke-Gate "$Wave Ruff" { & $Python -m ruff check ".\src\flowforge\phase$Wave" ".\tests\phase$Wave" }
    Invoke-Gate "$Wave Format" { & $Python -m ruff format --check ".\src\flowforge\phase$Wave" ".\tests\phase$Wave" }
    Invoke-Gate "$Wave Compile" { & $Python -m compileall -q ".\src\flowforge\phase$Wave" ".\tests\phase$Wave" }
    Invoke-Gate "$Wave MyPy" { & $Python -m mypy ".\src\flowforge\phase$Wave" }
    Invoke-Gate "$Wave Tests" { & $Python -m pytest -q ".\tests\phase$Wave" }
    Invoke-Gate "$Wave Full Regression" { & $Python -m pytest -q }
    if ($ApplyMigrations) {
        $Message = "phase $Wave $((Get-Content ".\manifests\phase$Wave.json" | ConvertFrom-Json).module)"
        Invoke-Gate "$Wave Migration Generation" { & $Python -m alembic revision --autogenerate -m $Message }
        $Migration = Get-ChildItem ".\migrations\versions" -File | Sort-Object LastWriteTime | Select-Object -Last 1
        Invoke-Gate "$Wave Migration Format" { & $Python -m ruff format $Migration.FullName }
        Invoke-Gate "$Wave Migration Lint" { & $Python -m ruff check $Migration.FullName --fix }
        Invoke-Gate "$Wave Upgrade" { & $Python -m alembic upgrade head }
        Invoke-Gate "$Wave RLS Generation" { & $Python ".\scripts\Generate-Tenant-RLS.py" }
        Get-Content ".\var\tenant_rls.sql" -Raw | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U flowforge -d flowforge
        if ($LASTEXITCODE -ne 0) { throw "$Wave RLS application failed" }
    }
    if ($CreateCheckpoints) {
        git add .
        git commit -m "Complete Phase $($Wave.ToUpper())"
        if ($LASTEXITCODE -ne 0) { throw "$Wave commit failed" }
        git tag -a $Tags[$Wave] -m "Phase $($Wave.ToUpper()) complete"
        if ($LASTEXITCODE -ne 0) { throw "$Wave tag failed" }
    }
}
Invoke-Gate "Final Ruff" { & $Python -m ruff check .\src .\tests }
Invoke-Gate "Final Format" { & $Python -m ruff format --check .\src .\tests }
Invoke-Gate "Final Compile" { & $Python -m compileall -q .\src .\tests }
Invoke-Gate "Final Tests" { & $Python -m pytest -q }
if ($CreateCheckpoints) {
    $FinalTag = "v4.9.0-phase4-complete"
    git tag -a $FinalTag -m "FlowForge Phase 4 complete"
    if ($LASTEXITCODE -ne 0) { throw "Final Phase 4 tag failed" }
}
Write-Host "FLOWFORGE REMAINING PHASE 4 BUILD PASSED" -ForegroundColor Green

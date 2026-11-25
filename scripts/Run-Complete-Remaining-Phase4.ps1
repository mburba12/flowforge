param([switch]$ApplyMigrations,[switch]$CreateCheckpoints)
$ErrorActionPreference="Stop"
$Python=".\.venv\Scripts\python.exe"
$Waves=@("4e","4f","4g","4h","4i","4j")
$Tags=@{"4e"="v4.4.0-phase4e-reconciliation";"4f"="v4.5.0-phase4f-copilot-documents";"4g"="v4.6.0-phase4g-governed-automation";"4h"="v4.7.0-phase4h-enterprise-controls";"4i"="v4.8.0-phase4i-production-connectors";"4j"="v4.9.0-phase4j-release-candidate"}
$Completed=@()
function Gate([string]$Name,[scriptblock]$Action){Write-Host "RUNNING: $Name" -ForegroundColor Cyan;& $Action;if($LASTEXITCODE -ne 0){Write-Host "FAILED WAVE: $Wave" -ForegroundColor Red;Write-Host "FAILED GATE: $Name" -ForegroundColor Red;Write-Host "LAST COMPLETED: $($Completed -join ', ')";git status --short;throw "$Name failed"};Write-Host "PASSED: $Name" -ForegroundColor Green}
foreach($Wave in $Waves){
 Write-Host "`n===== PHASE $($Wave.ToUpper()) =====" -ForegroundColor Yellow
 Gate "$Wave Ruff" {& $Python -m ruff check ".\src\flowforge\phase$Wave" ".\tests\phase$Wave"}
 Gate "$Wave Format" {& $Python -m ruff format --check ".\src\flowforge\phase$Wave" ".\tests\phase$Wave"}
 Gate "$Wave Compile" {& $Python -m compileall -q ".\src\flowforge\phase$Wave" ".\tests\phase$Wave"}
 Gate "$Wave MyPy" {& $Python -m mypy ".\src\flowforge\phase$Wave"}
 Gate "$Wave Focused Tests" {& $Python -m pytest -q ".\tests\phase$Wave"}
 Gate "$Wave Full Tests" {& $Python -m pytest -q}
 if($ApplyMigrations){
  $Existing=(Get-Content ".\manifests\phase$Wave.json" -Raw|ConvertFrom-Json).tables
  Gate "$Wave Migration" {& $Python -m alembic revision --autogenerate -m "phase $Wave continuous build"}
  $Migration=Get-ChildItem .\migrations\versions -File|Sort-Object LastWriteTime|Select-Object -Last 1
  Gate "$Wave Migration Format" {& $Python -m ruff format $Migration.FullName}
  Gate "$Wave Migration Lint" {& $Python -m ruff check $Migration.FullName --fix}
  Gate "$Wave Upgrade" {& $Python -m alembic upgrade head}
  Gate "$Wave RLS Generate" {& $Python .\scripts\Generate-Tenant-RLS.py}
  Get-Content .\var\tenant_rls.sql -Raw|docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U flowforge -d flowforge
  if($LASTEXITCODE -ne 0){throw "$Wave RLS failed"}
 }
 if($CreateCheckpoints){git add .;git commit -m "Complete Phase $($Wave.ToUpper())";if($LASTEXITCODE -ne 0){throw "$Wave commit failed"};git tag -a $Tags[$Wave] -m "Phase $($Wave.ToUpper()) complete";if($LASTEXITCODE -ne 0){throw "$Wave tag failed"}}
 $Completed+=$Wave
}
Gate "Final Ruff" {& $Python -m ruff check .\src .\tests}
Gate "Final Format" {& $Python -m ruff format --check .\src .\tests}
Gate "Final Compile" {& $Python -m compileall -q .\src .\tests}
Gate "Final Tests" {& $Python -m pytest -q}
if($CreateCheckpoints){git tag -a "v4.9.0-phase4-complete" -m "FlowForge Phase 4 complete"}
Write-Host "FLOWFORGE PHASE 4E-4J CONTINUOUS BUILD PASSED" -ForegroundColor Green

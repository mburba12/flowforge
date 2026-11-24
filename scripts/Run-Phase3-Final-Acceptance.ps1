$ErrorActionPreference="Stop"
$Base="http://127.0.0.1:8000"
$A=Invoke-RestMethod "$Base/phase3a/status"
$B=Invoke-RestMethod "$Base/phase3b/status"
$F=Invoke-RestMethod "$Base/phase3/status"
if($A.status-ne "implemented" -or $B.status-ne "implemented" -or $F.status-ne "integrated"){throw "Phase status failed"}
$Revision=docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT version_num FROM alembic_version;"
if($Revision.Trim()-ne "f6d88fb6e3eb"){throw "Unexpected revision: $Revision"}
$Count=docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
if([int]$Count.Trim()-lt 75){throw "Expected at least 75 tables"}
& ".\.venv\Scripts\python.exe" -m pytest -q tests/phase3a tests/phase3b tests/phase3final
if($LASTEXITCODE-ne 0){throw "Phase 3 regression failed"}
Write-Host "FLOWFORGE PHASE 3 FINAL ACCEPTANCE PASSED" -ForegroundColor Green

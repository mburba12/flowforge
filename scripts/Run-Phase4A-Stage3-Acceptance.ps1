$ErrorActionPreference="Stop"
$S=Invoke-RestMethod "http://127.0.0.1:8000/phase4a/stage3/status"
if($S.status-ne "implemented"){throw "Stage 3 status failed"}
& ".\.venv\Scripts\python.exe" -m pytest -q tests/phase4a tests/phase4a_stage2 tests/phase4a_stage3
if($LASTEXITCODE-ne 0){throw "Payroll regression failed"}
Write-Host "FLOWFORGE PHASE 4A STAGE 3 ACCEPTANCE PASSED" -ForegroundColor Green

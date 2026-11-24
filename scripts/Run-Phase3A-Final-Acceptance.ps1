$ErrorActionPreference="Stop"
$Base="http://127.0.0.1:8000"
$Status=Invoke-RestMethod "$Base/phase3a/status"
if($Status.status-ne "implemented"){throw "Phase 3A status failed"}
& ".\.venv\Scripts\python.exe" -m pytest -q tests/phase3a
if($LASTEXITCODE-ne 0){throw "Phase 3A regression failed"}
Write-Host "FLOWFORGE PHASE 3A FINAL ACCEPTANCE PASSED" -ForegroundColor Green

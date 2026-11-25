$ErrorActionPreference = "Stop"
$Status = Invoke-RestMethod "http://127.0.0.1:8000/phase4c/stage7/status"
if ($Status.status -ne "implemented") { throw "Status failed" }
if ($Status.providers.Count -ne 36) { throw "Provider coverage failed" }
& ".\.venv\Scripts\python.exe" -m pytest -q tests/phase4c_stage7
if ($LASTEXITCODE -ne 0) { throw "Regression failed" }
Write-Host "FLOWFORGE PHASE 4C STAGE 7 ENGAGEMENT ACCEPTANCE PASSED" -ForegroundColor Green

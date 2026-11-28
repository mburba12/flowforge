$ErrorActionPreference="Stop";Set-Location (Split-Path -Parent $PSScriptRoot);$P=".\.venv\Scripts\python.exe"
function G($N,$C){Write-Host "RUNNING: $N" -ForegroundColor Cyan;& $C;if($LASTEXITCODE-ne 0){throw "$N failed"};Write-Host "PASSED: $N" -ForegroundColor Green}
G "Compile" {& $P -m compileall -q src tests};G "Ruff" {& $P -m ruff check src tests};G "Format" {& $P -m ruff format --check src tests};G "MyPy Phase 3B" {& $P -m mypy src/flowforge/phase3b};G "Phase 3B tests" {& $P -m pytest -q tests/phase3b};Write-Host "PHASE 3B VERIFICATION PASSED" -ForegroundColor Green

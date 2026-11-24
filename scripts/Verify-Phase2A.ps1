$ErrorActionPreference="Stop";Set-Location (Split-Path -Parent $PSScriptRoot);$P=".\.venv\Scripts\python.exe"
function G($N,$C){Write-Host "RUNNING: $N" -ForegroundColor Cyan;& $C;if($LASTEXITCODE-ne 0){throw "$N failed"};Write-Host "PASSED: $N" -ForegroundColor Green}
G "Compile" {& $P -m compileall -q src tests};G "Ruff" {& $P -m ruff check src tests};G "Format" {& $P -m ruff format --check src tests};G "MyPy Phase 2A" {& $P -m mypy src/flowforge/phase2a};G "Phase 2A tests" {& $P -m pytest -q tests/phase2a};Write-Host "PHASE 2A VERIFICATION PASSED" -ForegroundColor Green

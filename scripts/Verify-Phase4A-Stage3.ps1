$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$P=".\.venv\Scripts\python.exe"
function G($N,$C){Write-Host "RUNNING: $N" -ForegroundColor Cyan;& $C;if($LASTEXITCODE-ne 0){throw "$N failed"};Write-Host "PASSED: $N" -ForegroundColor Green}
G "Compile" {& $P -m compileall -q src tests}
G "Ruff" {& $P -m ruff check src tests}
G "Format" {& $P -m ruff format --check src tests}
G "MyPy Stage 3" {& $P -m mypy src/flowforge/phase4a_stage3}
G "Stage 3 tests" {& $P -m pytest -q tests/phase4a_stage3}
Write-Host "PHASE 4A STAGE 3 VERIFICATION PASSED" -ForegroundColor Green

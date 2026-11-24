$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Python = ".\.venv\Scripts\python.exe"

function Gate($Name, $Command) {
    Write-Host "RUNNING: $Name" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
    Write-Host "PASSED: $Name" -ForegroundColor Green
}

Gate "Alembic upgrade" { & $Python -m alembic upgrade head }
Gate "Compile" { & $Python -m compileall -q src tests }
Gate "Ruff" { & $Python -m ruff check src tests }
Gate "Format" { & $Python -m ruff format --check src tests }
Gate "MyPy Phase 2A" { & $Python -m mypy src/flowforge/phase2a }
Gate "MyPy Phase 2B" { & $Python -m mypy src/flowforge/phase2b }
Gate "Phase 2A tests" { & $Python -m pytest -q tests/phase2a }
Gate "Phase 2B tests" { & $Python -m pytest -q tests/phase2b }
Gate "Full regression" { & $Python -m pytest -q }
Write-Host "PHASE 2 FINAL INTEGRATION BUILD PASSED" -ForegroundColor Green

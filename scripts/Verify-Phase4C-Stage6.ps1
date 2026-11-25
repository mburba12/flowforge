$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Python = ".\.venv\Scripts\python.exe"
& $Python -m compileall -q src tests
if ($LASTEXITCODE -ne 0) { throw "Compile failed" }
& $Python -m ruff check src tests
if ($LASTEXITCODE -ne 0) { throw "Ruff failed" }
& $Python -m ruff format --check src tests
if ($LASTEXITCODE -ne 0) { throw "Format failed" }
& $Python -m mypy src/flowforge/phase4c_stage6
if ($LASTEXITCODE -ne 0) { throw "MyPy failed" }
& $Python -m pytest -q tests/phase4c_stage6
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
Write-Host "PHASE 4C STAGE 6 VERIFICATION PASSED" -ForegroundColor Green

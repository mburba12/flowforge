$ErrorActionPreference="Stop";Set-Location (Split-Path -Parent $PSScriptRoot);$Python=".\.venv\Scripts\python.exe"
& $Python -m ruff check src/flowforge/phase1a tests/phase1a --fix
& $Python -m ruff format src/flowforge/phase1a tests/phase1a
& $Python -m mypy src/flowforge/phase1a
& $Python -m pytest -q tests/phase1a
if($LASTEXITCODE-ne 0){throw "Phase 1A verification failed"}
Write-Host "PHASE 1A PACKAGE INSTALLED AND VERIFIED" -ForegroundColor Green

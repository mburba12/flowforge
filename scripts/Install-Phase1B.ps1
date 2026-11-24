$ErrorActionPreference="Stop";Set-Location (Split-Path -Parent $PSScriptRoot);$P=".\.venv\Scripts\python.exe"
& $P -m ruff check src/flowforge/phase1b tests/phase1b --fix
& $P -m ruff format src/flowforge/phase1b tests/phase1b
& $P -m mypy src/flowforge/phase1b
& $P -m pytest -q tests/phase1b
if($LASTEXITCODE-ne 0){throw "Phase 1B verification failed"}
Write-Host "PHASE 1B PACKAGE INSTALLED AND VERIFIED" -ForegroundColor Green

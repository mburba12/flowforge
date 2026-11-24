$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Python = ".\.venv\Scripts\python.exe"
& $Python -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& $Python -m ruff check src tests --fix
& $Python -m ruff format src tests
Write-Host "Phase 1 total file pack installed." -ForegroundColor Green

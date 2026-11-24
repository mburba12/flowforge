$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
if (-not (Test-Path ".venv")) { py -3.12 -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"
docker compose up -d postgres
Write-Host "FlowForge Phase 1 installed." -ForegroundColor Green
Write-Host "Next: .\scripts\Verify-Phase1.ps1" -ForegroundColor Cyan

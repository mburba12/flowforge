$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Python = ".\.venv\Scripts\python.exe"
& $Python .\scripts\Generate-Tenant-RLS.py
if ($LASTEXITCODE -ne 0) { throw "RLS generation failed." }
Get-Content .\var\tenant_rls.sql -Raw | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U flowforge -d flowforge
if ($LASTEXITCODE -ne 0) { throw "RLS installation failed." }
& .\scripts\Verify-Phase4-Security.ps1

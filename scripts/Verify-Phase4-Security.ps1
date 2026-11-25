$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Python = ".\.venv\Scripts\python.exe"
& $Python -m compileall -q src tests
if ($LASTEXITCODE -ne 0) { throw "Compile failed." }
& $Python -m ruff check src tests
if ($LASTEXITCODE -ne 0) { throw "Ruff failed." }
& $Python -m ruff format --check src tests
if ($LASTEXITCODE -ne 0) { throw "Format failed." }
& $Python -m mypy src\flowforge\security_hardening
if ($LASTEXITCODE -ne 0) { throw "MyPy failed." }
& $Python -m pytest -q tests\security_hardening
if ($LASTEXITCODE -ne 0) { throw "Security tests failed." }
$Missing = docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT count(*) FROM information_schema.tables t WHERE t.table_schema='public' AND EXISTS (SELECT 1 FROM information_schema.columns c WHERE c.table_schema=t.table_schema AND c.table_name=t.table_name AND c.column_name='tenant_id') AND NOT EXISTS (SELECT 1 FROM pg_class pc JOIN pg_namespace pn ON pn.oid=pc.relnamespace WHERE pn.nspname=t.table_schema AND pc.relname=t.table_name AND pc.relrowsecurity AND pc.relforcerowsecurity);"
if ([int]$Missing.Trim() -ne 0) { throw "Tenant tables missing forced RLS: $Missing" }
Write-Host "FLOWFORGE TENANT ISOLATION SECURITY GATE PASSED" -ForegroundColor Green

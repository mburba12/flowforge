$ErrorActionPreference="Stop";Set-Location (Split-Path -Parent $PSScriptRoot);$Python=".\.venv\Scripts\python.exe"
function Run($n,$c){Write-Host "RUNNING: $n" -ForegroundColor Cyan;& $c;if($LASTEXITCODE-ne 0){throw "$n failed"};Write-Host "PASSED: $n" -ForegroundColor Green}
Run "Compile" {& $Python -m compileall -q src tests};Run "Ruff" {& $Python -m ruff check src tests};Run "Format" {& $Python -m ruff format --check src tests};Run "MyPy" {& $Python -m mypy src};Run "Tests" {& $Python -m pytest -q};Write-Host "PHASE 1 COMPLETE" -ForegroundColor Green

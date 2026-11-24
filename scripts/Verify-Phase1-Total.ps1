$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Python = ".\.venv\Scripts\python.exe"
function Gate($Name,$Command){ Write-Host "RUNNING: $Name" -ForegroundColor Cyan; & $Command; if($LASTEXITCODE -ne 0){throw "$Name failed"}; Write-Host "PASSED: $Name" -ForegroundColor Green }
Gate "Compile" { & $Python -m compileall -q src tests }
Gate "Ruff" { & $Python -m ruff check src tests }
Gate "Format" { & $Python -m ruff format --check src tests }
Gate "MyPy" { & $Python -m mypy src }
Gate "Tests" { & $Python -m pytest -q }
Write-Host "PHASE 1 TOTAL FILE VERIFICATION PASSED" -ForegroundColor Green

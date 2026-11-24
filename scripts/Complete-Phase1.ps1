$ErrorActionPreference="Stop"; Set-Location (Split-Path -Parent $PSScriptRoot); $Python=".\.venv\Scripts\python.exe"
& $Python -m pip install -e ".[dev]"; if($LASTEXITCODE-ne 0){throw "Install failed"}
& $Python -m ruff check src tests --fix; & $Python -m ruff format src tests
& $Python -m alembic revision --autogenerate -m "complete phase 1"; if($LASTEXITCODE-ne 0){throw "Migration generation failed"}
& $Python -m alembic upgrade head; if($LASTEXITCODE-ne 0){throw "Migration upgrade failed"}
& ".\scripts\Verify-Phase1.ps1"

$ErrorActionPreference="Stop";Set-Location (Split-Path -Parent $PSScriptRoot);$Python=".\.venv\Scripts\python.exe"
$Main=".\src\flowforge\main.py";$Text=[IO.File]::ReadAllText((Resolve-Path $Main))
if(-not $Text.Contains("from flowforge.integration.router import router as phase1_router")){$Text=$Text.Replace("from flowforge.api.router import api_router","from flowforge.api.router import api_router`r`nfrom flowforge.integration.router import router as phase1_router")}
if(-not $Text.Contains("app.include_router(phase1_router)")){$Text=$Text+"`r`napp.include_router(phase1_router)`r`n"}
[IO.File]::WriteAllText((Resolve-Path $Main),$Text,[Text.UTF8Encoding]::new($false))
& $Python -m ruff check src tests --fix; if($LASTEXITCODE-ne 0){throw "Ruff fix failed"}
& $Python -m ruff format src tests; if($LASTEXITCODE-ne 0){throw "Format failed"}
& $Python -m alembic revision --autogenerate -m "integrate phase 1a and phase 1b";if($LASTEXITCODE-ne 0){throw "Migration generation failed"}
& $Python -m alembic upgrade head;if($LASTEXITCODE-ne 0){throw "Migration upgrade failed"}
& ".\scripts\Verify-Phase1-Integration.ps1"

$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$P=".\.venv\Scripts\python.exe"
$M=".\src\flowforge\main.py"
$T=[IO.File]::ReadAllText((Resolve-Path $M))
$I="from flowforge.phase3final.router import router as phase3_final_router"
if(-not $T.Contains($I)){$T=$T.Replace("from flowforge.api.router import api_router","from flowforge.api.router import api_router`r`n$I")}
if(-not $T.Contains("app.include_router(phase3_final_router)")){$T+="`r`napp.include_router(phase3_final_router)`r`n"}
[IO.File]::WriteAllText((Resolve-Path $M),$T,[Text.UTF8Encoding]::new($false))
& $P -m ruff check src/flowforge/phase3final tests/phase3final src/flowforge/main.py --fix
if($LASTEXITCODE-ne 0){throw "Ruff failed"}
& $P -m ruff format src/flowforge/phase3final tests/phase3final src/flowforge/main.py
& $P -m compileall -q src tests
if($LASTEXITCODE-ne 0){throw "Compile failed"}
& $P -m mypy src/flowforge/phase3final
if($LASTEXITCODE-ne 0){throw "MyPy failed"}
& $P -m pytest -q tests/phase3a tests/phase3b tests/phase3final
if($LASTEXITCODE-ne 0){throw "Phase 3 tests failed"}
Write-Host "PHASE 3 FINAL INTEGRATION BUILD PASSED" -ForegroundColor Green

$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$P=".\.venv\Scripts\python.exe"
$R=".\src\flowforge\phase3a\router.py"
$T=[IO.File]::ReadAllText((Resolve-Path $R))
if(-not $T.Contains("from .payment_routes import router as payment_router")){
  $T=$T.Replace("from .routes import router as routes","from .routes import router as routes`r`nfrom .payment_routes import router as payment_router")
}
if(-not $T.Contains("router.include_router(payment_router)")){$T+="`r`nrouter.include_router(payment_router)`r`n"}
[IO.File]::WriteAllText((Resolve-Path $R),$T,[Text.UTF8Encoding]::new($false))
& $P -m ruff check src/flowforge/phase3a tests/phase3a --fix
if($LASTEXITCODE-ne 0){throw "Ruff failed"}
& $P -m ruff format src/flowforge/phase3a tests/phase3a
& $P -m mypy src/flowforge/phase3a
if($LASTEXITCODE-ne 0){throw "MyPy failed"}
& $P -m pytest -q tests/phase3a
if($LASTEXITCODE-ne 0){throw "Tests failed"}
Write-Host "PHASE 3A FINAL BUILD PASSED" -ForegroundColor Green

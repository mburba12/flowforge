$ErrorActionPreference="Stop"
$Python=".\.venv\Scripts\python.exe"
& $Python -m ruff check .\src\flowforge\phase5b .\tests\phase5b
if($LASTEXITCODE-ne 0){throw "Ruff failed"}
& $Python -m ruff format --check .\src\flowforge\phase5b .\tests\phase5b
if($LASTEXITCODE-ne 0){throw "Format failed"}
& $Python -m mypy .\src\flowforge\phase5b
if($LASTEXITCODE-ne 0){throw "MyPy failed"}
& $Python -m pytest -q .\tests\phase5b
if($LASTEXITCODE-ne 0){throw "Focused tests failed"}
& $Python -m pytest -q
if($LASTEXITCODE-ne 0){throw "Regression failed"}
Push-Location .\web
try{npm ci;npm audit --audit-level=high;npm run typecheck;npm test;npm run build;npm run test:e2e}finally{Pop-Location}
if($LASTEXITCODE-ne 0){throw "Frontend failed"}
az bicep build --file .\infra\bicep\main.bicep
if($LASTEXITCODE-ne 0){throw "Bicep failed"}
Write-Host "FLOWFORGE PHASE 5B OFFLINE IMPLEMENTATION GATE PASSED" -ForegroundColor Green

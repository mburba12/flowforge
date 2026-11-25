$ErrorActionPreference="Stop"
$Python=".\.venv\Scripts\python.exe"
& $Python -m ruff check .\src\flowforge\phase5a .\tests\phase5a
if($LASTEXITCODE-ne 0){throw "Ruff failed"}
& $Python -m mypy .\src\flowforge\phase5a
if($LASTEXITCODE-ne 0){throw "MyPy failed"}
& $Python -m pytest -q .\tests\phase5a
if($LASTEXITCODE-ne 0){throw "Backend tests failed"}
Push-Location .\web
try{npm ci;npm run typecheck;npm test;npm run build;npx playwright test}finally{Pop-Location}
if($LASTEXITCODE-ne 0){throw "Frontend gate failed"}
Write-Host "FLOWFORGE PHASE 5A VALIDATION PASSED" -ForegroundColor Green

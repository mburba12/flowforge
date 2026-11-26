$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\Users\mackb\Downloads\Download the FlowForge Phase 1 scaffold\flowforge-phase1"
Set-Location $ProjectRoot
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Missing virtual environment" }

docker compose up -d
if ($LASTEXITCODE -ne 0) { throw "Local infrastructure failed" }

& $Python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw "Database migration failed" }

& $Python -m ruff check .\src .\tests .\migrations\env.py
if ($LASTEXITCODE -ne 0) { throw "Ruff failed" }
& $Python -m ruff format --check .\src .\tests .\migrations\env.py
if ($LASTEXITCODE -ne 0) { throw "Formatting failed" }
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Backend tests failed" }

Push-Location .\web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "TypeScript failed" }
    npm test
    if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed" }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
} finally { Pop-Location }

Write-Host "FLOWFORGE UNIFIED LOCAL BUILD PASSED" -ForegroundColor Green
Write-Host "External provider writes remain locked by activation policy." -ForegroundColor Yellow

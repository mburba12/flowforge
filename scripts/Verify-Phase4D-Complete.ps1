$ErrorActionPreference = "Stop"
$Python = ".\.venv\Scripts\python.exe"
& $Python -m ruff check .\src\flowforge\phase4d .\tests\phase4d
if ($LASTEXITCODE -ne 0) { throw "Ruff failed" }
& $Python -m ruff format --check .\src\flowforge\phase4d .\tests\phase4d
if ($LASTEXITCODE -ne 0) { throw "Format failed" }
& $Python -m compileall -q .\src\flowforge\phase4d .\tests\phase4d
if ($LASTEXITCODE -ne 0) { throw "Compile failed" }
& $Python -m mypy .\src\flowforge\phase4d
if ($LASTEXITCODE -ne 0) { throw "MyPy failed" }
& $Python -m pytest -q .\tests\phase4d
if ($LASTEXITCODE -ne 0) { throw "Focused tests failed" }
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Regression failed" }
Write-Host "PHASE 4D FEATURE IMPLEMENTATION GATE PASSED" -ForegroundColor Green

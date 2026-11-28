[CmdletBinding()]param([string]$ProjectRoot=(Get-Location).Path)
$ErrorActionPreference="Stop";Set-Location $ProjectRoot;$py=".\.venv\Scripts\python.exe"
&$py -m ruff check src tests;if($LASTEXITCODE){throw "Ruff failed"}
&$py -m mypy src/flowforge;if($LASTEXITCODE){throw "MyPy failed"}
&$py -m pytest -q;if($LASTEXITCODE){throw "Pytest failed"}
Push-Location web;try{npm run typecheck;if($LASTEXITCODE){throw "Typecheck failed"};npm run lint;if($LASTEXITCODE){throw "Lint failed"};npm test -- --run;if($LASTEXITCODE){throw "Tests failed"};npm run build;if($LASTEXITCODE){throw "Build failed"}}finally{Pop-Location}
Write-Host "FLOWFORGE PART 2B ACCEPTANCE PASSED" -ForegroundColor Green

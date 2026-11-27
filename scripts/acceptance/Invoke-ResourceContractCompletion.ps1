[CmdletBinding()]param([string]$ProjectRoot=(Get-Location).Path)
$ErrorActionPreference='Stop';Set-Location $ProjectRoot;$py='.\.venv\Scripts\python.exe'
&$py -m ruff check src/flowforge/resource_contracts tests/resource_contracts;if($LASTEXITCODE){throw 'Ruff failed'}
&$py -m mypy src/flowforge/resource_contracts;if($LASTEXITCODE){throw 'MyPy failed'}
&$py -m pytest -q tests/resource_contracts;if($LASTEXITCODE){throw 'Contract tests failed'}
Push-Location web;try{npm run typecheck;if($LASTEXITCODE){throw 'Typecheck failed'};npm run lint;if($LASTEXITCODE){throw 'Lint failed'};npm run build;if($LASTEXITCODE){throw 'Build failed'}}finally{Pop-Location}
Write-Host 'FLOWFORGE RESOURCE-CONTRACT COMPLETION ACCEPTANCE PASSED' -ForegroundColor Green

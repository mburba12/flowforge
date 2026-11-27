[CmdletBinding()]param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference='Stop';Set-Location $ProjectRoot;$Py=Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$steps=@(
 @('Compile',{$args[0] -m compileall -q src/flowforge}),
 @('Ruff',{$args[0] -m ruff check src tests migrations}),
 @('MyPy',{$args[0] -m mypy src/flowforge}),
 @('Tests',{$args[0] -m pytest -q}),
 @('Alembic heads',{$args[0] -m alembic heads}),
 @('Alembic upgrade',{$args[0] -m alembic upgrade head})
)
foreach($s in $steps){Write-Host "RUNNING: $($s[0])" -ForegroundColor Cyan;& $s[1] $Py;if($LASTEXITCODE -ne 0){throw "$($s[0]) failed"};Write-Host "PASSED: $($s[0])" -ForegroundColor Green}
Push-Location web
try{npm.cmd ci;if($LASTEXITCODE){throw 'npm ci failed'};npm.cmd run lint;if($LASTEXITCODE){throw 'frontend lint failed'};npm.cmd run typecheck;if($LASTEXITCODE){throw 'frontend typecheck failed'};npm.cmd test -- --run;if($LASTEXITCODE){throw 'frontend tests failed'};npm.cmd run build;if($LASTEXITCODE){throw 'frontend build failed'}}finally{Pop-Location}
Write-Host 'FLOWFORGE BG-14 STRUCTURAL ACCEPTANCE PASSED' -ForegroundColor Green
Write-Host 'Live four-tenant, provider, failure-recovery, and cleanup certification still require running environments.' -ForegroundColor Yellow

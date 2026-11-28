$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path;Set-Location $root
$mapped=@('ap','ar','orders','inventory','banking','finance','payroll','workforce','tax','reconciliation','integrations','entities','documents','audit')
$fail=@();foreach($route in $mapped){$p="web\src\app\$route\page.tsx";$t=Get-Content $p -Raw;if($t -notmatch 'BackendFeatureWorkspace'){$fail+=$p}}
if($fail){$fail;throw 'Mapped routes missing live workspace'}
$demo=git grep -n 'demo-data' -- 'web/src/app/*.tsx' 'web/src/app/*/page.tsx' 2>$null;if($LASTEXITCODE -gt 1){throw 'git grep failed'}
if($demo){$demo;throw 'Production routes still import demo-data'}
Write-Host 'FLOWFORGE PART 1 CONNECTION AUDIT PASSED' -ForegroundColor Green

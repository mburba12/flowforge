[CmdletBinding()]
param([string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference='Stop'; Set-Location $ProjectRoot
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'
foreach($name in @('refine_registry.py','generate_build_queue.py')){
 Write-Host "RUNNING: $name" -ForegroundColor Cyan
 & $Python (Join-Path $PSScriptRoot $name) --root $ProjectRoot
 if($LASTEXITCODE -ne 0){throw "$name failed"}
 Write-Host "PASSED: $name" -ForegroundColor Green
}
& $Python (Join-Path $PSScriptRoot 'finalize_review.py') --root $ProjectRoot --allow-pending
if($LASTEXITCODE -ne 0){throw 'BG-00 review baseline validation failed'}
Write-Host 'FLOWFORGE BG-00 REFINEMENT BASELINE PASSED' -ForegroundColor Green
Write-Host 'Manual review remains required before BG-00 COMPLETE can be claimed.' -ForegroundColor Yellow

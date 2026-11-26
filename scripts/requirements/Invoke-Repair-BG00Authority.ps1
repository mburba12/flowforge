[CmdletBinding()]param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference='Stop';Set-Location $ProjectRoot;$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe'
& $Python (Join-Path $PSScriptRoot 'rebuild_registry_from_blueprint.py') --root $ProjectRoot
if($LASTEXITCODE -ne 0){throw 'Blueprint registry rebuild failed'}
& $Python (Join-Path $PSScriptRoot 'validate_bg00_authority.py') --root $ProjectRoot
if($LASTEXITCODE -ne 0){throw 'BG-00 authority validation failed'}
Write-Host 'FLOWFORGE BG-00 AUTHORITATIVE REGISTRY REPAIRED' -ForegroundColor Green
Write-Host 'Artifact, dependency, and evidence reviews remain pending and must not be auto-approved.' -ForegroundColor Yellow

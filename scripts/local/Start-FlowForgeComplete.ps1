[CmdletBinding()]param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference='Stop';Set-Location -LiteralPath $ProjectRoot
docker compose -f docker-compose.yml -f docker-compose.phase-c.yml up -d --build
if($LASTEXITCODE -ne 0){throw 'Startup failed'}
Write-Host 'FlowForge: http://127.0.0.1:3000' -ForegroundColor Green
Write-Host 'API docs: http://127.0.0.1:8000/docs' -ForegroundColor Green
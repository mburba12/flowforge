[CmdletBinding()]
param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,[switch]$WithLocalDependencies)
$ErrorActionPreference="Stop"; Set-StrictMode -Version Latest; Set-Location $ProjectRoot
if(-not (Get-Command docker -ErrorAction SilentlyContinue)){throw "Docker is not available."}
if(-not (Test-Path ".\.env")){throw ".env is missing."}
$Args=@("compose")
if($WithLocalDependencies -and (Test-Path ".\docker-compose.local.yml")){$Args+=@("-f","docker-compose.yml","-f","docker-compose.local.yml")}
$Args+=@("up","-d","--build")
& docker @Args
if($LASTEXITCODE -ne 0){throw "Docker Compose startup failed."}
$Deadline=(Get-Date).AddMinutes(3); $Healthy=$false
while((Get-Date)-lt $Deadline){try{$r=Invoke-RestMethod "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 5;if($r.status -eq "ok"){$Healthy=$true;break}}catch{};Start-Sleep 2}
if(-not $Healthy){docker compose logs --tail 100 api;throw "API did not become healthy."}
$Role=& docker compose exec -T api python -c "from flowforge.core.config import settings; from sqlalchemy.engine import make_url; print(make_url(settings.database_url).username)"
if($LASTEXITCODE -ne 0 -or $Role[-1].Trim() -ne "flowforge_app"){throw "API is not using flowforge_app."}
Write-Host "FLOWFORGE LOCAL SERVER STARTED" -ForegroundColor Green
Write-Host "API: http://127.0.0.1:8000"; Write-Host "OpenAPI: http://127.0.0.1:8000/docs"

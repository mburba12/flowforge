[CmdletBinding()]
param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path)
$ErrorActionPreference="Stop"; Set-Location $ProjectRoot
docker compose up -d --force-recreate api
if($LASTEXITCODE -ne 0){throw "API restart failed."}
$Deadline=(Get-Date).AddMinutes(2); do{try{$r=Invoke-RestMethod "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 5;if($r.status -eq "ok"){Write-Host "FLOWFORGE API RESTARTED" -ForegroundColor Green;exit 0}}catch{};Start-Sleep 2}while((Get-Date)-lt $Deadline)
throw "API did not recover after restart."

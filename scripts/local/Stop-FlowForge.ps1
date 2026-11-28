[CmdletBinding()]
param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,[switch]$All)
$ErrorActionPreference="Stop"; Set-Location $ProjectRoot
if($All){docker compose stop}else{docker compose stop api}
if($LASTEXITCODE -ne 0){throw "FlowForge shutdown failed."}
Write-Host "FLOWFORGE STOPPED; DATA VOLUMES PRESERVED" -ForegroundColor Green

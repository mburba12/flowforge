<#
.SYNOPSIS  Start (or update) the FlowForge production stack and wait until it is healthy.
.EXAMPLE   .\scripts\production\Start-FlowForge.ps1
#>
[CmdletBinding()]
param([string]$Project = "flowforge", [string]$EnvFile, [switch]$Build)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
if (-not $EnvFile) { $EnvFile = Join-Path (Get-FFRoot) ".env.production" }
$cfg = Read-FFEnvFile $EnvFile
$apiPort = if ($env:FF_API_PORT) { $env:FF_API_PORT } else { $cfg["FF_API_PORT"] }
$webPort = if ($env:FF_WEB_PORT) { $env:FF_WEB_PORT } else { $cfg["FF_WEB_PORT"] }

$composeArgs = @("up", "-d", "--wait")
if ($Build) { $composeArgs += "--build" }
Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments $composeArgs -Description "Start $Project" | Out-Null
Wait-FFHttp "http://127.0.0.1:$apiPort/api/v1/health"
Wait-FFHttp "http://127.0.0.1:$webPort/login"
Write-Host "FLOWFORGE RUNNING: web http://127.0.0.1:$webPort  api http://127.0.0.1:$apiPort" -ForegroundColor Green

<#
.SYNOPSIS  Stop the FlowForge production stack. Data volumes are always kept (never "down -v").
#>
[CmdletBinding()]
param([string]$Project = "flowforge", [string]$EnvFile)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
if (-not $EnvFile) { $EnvFile = Join-Path (Get-FFRoot) ".env.production" }
Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments @("stop") -Description "Stop $Project" | Out-Null
Write-Host "FLOWFORGE STOPPED (data volumes kept)"

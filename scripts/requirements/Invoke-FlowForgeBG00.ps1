[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$MegaSpecification,
    [string]$UltimateSpecification,
    [string]$EnterpriseBible,
    [string]$Blueprint,
    [string]$CapabilityInventory
)
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { $Python = (Get-Command python).Source }
$Source = Join-Path $ProjectRoot 'specs\source'
New-Item -ItemType Directory -Path $Source -Force | Out-Null
$copies = @(
    @($MegaSpecification,'FlowForge_Mega_Specification_Volume.pdf'),
    @($UltimateSpecification,'FlowForge_Ultimate_Master_Specification.pdf'),
    @($EnterpriseBible,'FlowForge_Enterprise_Build_Bible.pdf'),
    @($Blueprint,'FlowForge_AI_Completion_and_Deployment_Blueprint.pdf'),
    @($CapabilityInventory,'FLOWFORGE_CURRENT_CAPABILITIES.txt')
)
foreach ($pair in $copies) {
    if (-not [string]::IsNullOrWhiteSpace($pair[0])) {
        if (-not (Test-Path -LiteralPath $pair[0] -PathType Leaf)) { throw "Source file missing: $($pair[0])" }
        Copy-Item -LiteralPath $pair[0] -Destination (Join-Path $Source $pair[1]) -Force
    }
}
foreach ($name in @('FlowForge_Mega_Specification_Volume.pdf','FlowForge_Ultimate_Master_Specification.pdf','FlowForge_Enterprise_Build_Bible.pdf')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Source $name) -PathType Leaf)) { throw "Required PDF missing from specs/source: $name" }
}
$steps = @(
    @('extract_requirements.py',@('--root',$ProjectRoot)),
    @('build_registry.py',@('--root',$ProjectRoot)),
    @('crosswalk_repository.py',@('--root',$ProjectRoot)),
    @('validate_registry.py',@('--root',$ProjectRoot))
)
foreach ($step in $steps) {
    $script = Join-Path $ProjectRoot ('scripts\requirements\' + $step[0])
    Write-Host "RUNNING: $($step[0])" -ForegroundColor Cyan
    & $Python $script @($step[1])
    if ($LASTEXITCODE -ne 0) { throw "$($step[0]) failed with exit code $LASTEXITCODE" }
    Write-Host "PASSED: $($step[0])" -ForegroundColor Green
}
Write-Host ''
Write-Host 'FLOWFORGE BG-00 REQUIREMENT REGISTRY FOUNDATION PASSED' -ForegroundColor Green

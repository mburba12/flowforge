# Production stack entry point (since the 2026-11-27 cutover). See docs\FLOWFORGE_PRODUCTION_RUNBOOK.md.
# The pre-cutover recovered runtime is retired; use scripts\production\Rollback-FlowForgeCutover.ps1 to return to it.
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "scripts\production\Start-FlowForge.ps1") @args

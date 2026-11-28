<#
.SYNOPSIS  Back up the production database, verify it, encrypt it, copy it off this computer.
.DESCRIPTION
    pg_dump (custom format) -> verified -> encrypted with FLOWFORGE_BACKUP_KEY (AES-256-GCM,
    scripts\production\ffcrypt.py) -> the plain dump is deleted -> a copy goes to
    FLOWFORGE_BACKUP_OFFSITE_DIR (for example a OneDrive folder) when set.
    Daily backups are kept for 30 days in both places; other labels are kept.
    Restore: decrypt first (see docs\FLOWFORGE_PRODUCTION_RUNBOOK.md, "Backup and restore").
.OUTPUTS   Path of the verified (encrypted) backup under var\backups.
#>
[CmdletBinding()]
param([string]$Project = "flowforge", [string]$Label = "manual", [string]$EnvFile)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
if (-not $EnvFile) { $EnvFile = Join-Path (Get-FFRoot) ".env.production" }
$cfg = Read-FFEnvFile $EnvFile
$db = Get-FFContainer $Project "db"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dir = Join-Path (Get-FFRoot) "var\backups"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$inContainer = "/tmp/flowforge-$Label-$stamp.dump"
$hostPath = Join-Path $dir "flowforge-$Project-$Label-$stamp.dump"
Invoke-FFNative -Description "pg_dump" -Command { docker exec $db pg_dump -U flowforge_owner -d flowforge -Fc -f $inContainer } | Out-Null
try {
    Invoke-FFNative -Description "Copy backup" -Command { docker cp "${db}:$inContainer" $hostPath } | Out-Null
    $entries = Invoke-FFNative -Description "Verify backup" -Command { docker exec $db sh -c "pg_restore -l $inContainer | grep -c 'TABLE DATA'" }
} finally {
    docker exec $db rm -f $inContainer | Out-Null
}
$size = (Get-Item -LiteralPath $hostPath).Length
if ($size -le 0 -or [int]($entries | Select-Object -Last 1) -le 0) { throw "Backup verification failed: $hostPath" }

$result = $hostPath
if ($cfg["FLOWFORGE_BACKUP_KEY"]) {
    $result = Protect-FFFile $hostPath $cfg["FLOWFORGE_BACKUP_KEY"]
} else {
    Write-Warning "FLOWFORGE_BACKUP_KEY is not set: this backup is NOT encrypted (run Complete-FlowForgeSecurity.ps1)."
}
Write-Host ("BACKUP VERIFIED: {0} ({1} bytes, {2} table-data entries{3})" -f $result, $size, ($entries | Select-Object -Last 1), $(if ($result -ne $hostPath) { ", encrypted" } else { "" })) -ForegroundColor Green

$offsite = $cfg["FLOWFORGE_BACKUP_OFFSITE_DIR"]
if ($offsite -and $result -ne $hostPath) {
    try {
        New-Item -ItemType Directory -Force -Path $offsite | Out-Null
        Copy-Item -LiteralPath $result -Destination $offsite -Force
        Write-Host "Copied off this computer to $offsite"
    } catch {
        Write-Warning "Could not copy the backup to ${offsite}: $($_.Exception.Message)"
    }
}
# Keep 30 days of daily backups (other labels, such as pre-update backups, are kept).
$cutoff = (Get-Date).AddDays(-30)
foreach ($folder in @($dir, $offsite) | Where-Object { $_ -and (Test-Path $_) }) {
    Get-ChildItem -LiteralPath $folder -Filter "flowforge-*-daily-*" -File |
        Where-Object { $_.LastWriteTime -lt $cutoff } |
        Remove-Item -Force -Confirm:$false -ErrorAction SilentlyContinue
}
$result

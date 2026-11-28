<#
.SYNOPSIS  Back up the production database (pg_dump custom format) and verify the dump.
.OUTPUTS   Path of the verified backup under var\backups (gitignored).
#>
[CmdletBinding()]
param([string]$Project = "flowforge", [string]$Label = "manual")
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
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
Write-Host ("BACKUP VERIFIED: {0} ({1} bytes, {2} table-data entries)" -f $hostPath, $size, ($entries | Select-Object -Last 1)) -ForegroundColor Green
$hostPath

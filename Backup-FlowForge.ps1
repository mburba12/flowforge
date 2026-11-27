$ErrorActionPreference = "Stop"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Output = Join-Path $HOME "Downloads\forgeflow-$Timestamp.sql"
cmd /c "docker exec forgeflow-v4-phase0-postgres-1 pg_dump -U forgeflow -d forgeflow --clean --if-exists --no-owner --no-privileges > `"$Output`""
if ($LASTEXITCODE -ne 0) {
    throw "Backup failed."
}
Write-Host "BACKUP CREATED: $Output" -ForegroundColor Green

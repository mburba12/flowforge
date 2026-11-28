[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $ProjectRoot

$Timestamp = Get-Date -Format "yyyyMMddHHmmss"
$RestoreDatabase = "flowforge_restore_test_$Timestamp"
$ContainerDump = "/tmp/flowforge_backup_$Timestamp.dump"
$HostBackupDirectory = Join-Path $ProjectRoot "var\backups"
$HostDump = Join-Path $HostBackupDirectory "flowforge_backup_$Timestamp.dump"
$RestoreCreated = $false

New-Item -ItemType Directory -Force -Path $HostBackupDirectory | Out-Null

try {
    Write-Host "RUNNING: PostgreSQL backup" -ForegroundColor Cyan

    docker compose exec -T postgres pg_dump -U flowforge -d flowforge -Fc -f $ContainerDump

    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL backup failed."
    }

    docker compose cp "postgres:$ContainerDump" $HostDump

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to copy the backup from PostgreSQL."
    }

    $BackupFile = Get-Item -LiteralPath $HostDump

    if ($BackupFile.Length -le 0) {
        throw "Backup file is empty."
    }

    $BackupHash = (Get-FileHash -LiteralPath $HostDump -Algorithm SHA256).Hash

    Write-Host "PASSED: Backup created" -ForegroundColor Green
    Write-Host "Backup file: $HostDump"
    Write-Host "Backup bytes: $($BackupFile.Length)"
    Write-Host "SHA256: $BackupHash"

    Write-Host "RUNNING: Temporary restore database creation" -ForegroundColor Cyan

    docker compose exec -T postgres createdb -U flowforge $RestoreDatabase

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create the temporary restore database."
    }

    $RestoreCreated = $true

    docker compose exec -T postgres pg_restore -U flowforge -d $RestoreDatabase --no-owner --no-privileges $ContainerDump

    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL restore failed."
    }

    Write-Host "PASSED: Backup restored into $RestoreDatabase" -ForegroundColor Green

    Write-Host "RUNNING: Source and restored database comparison" -ForegroundColor Cyan

    $SourceTableCount = (docker compose exec -T postgres psql -U flowforge -d flowforge -At -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';").Trim()

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to count source database tables."
    }

    $RestoredTableCount = (docker compose exec -T postgres psql -U flowforge -d $RestoreDatabase -At -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';").Trim()

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to count restored database tables."
    }

    if ($SourceTableCount -ne $RestoredTableCount) {
        throw "Table-count mismatch. Source=$SourceTableCount Restored=$RestoredTableCount"
    }

    $SourceMigration = (docker compose exec -T postgres psql -U flowforge -d flowforge -At -c "SELECT version_num FROM alembic_version;").Trim()
    $RestoredMigration = (docker compose exec -T postgres psql -U flowforge -d $RestoreDatabase -At -c "SELECT version_num FROM alembic_version;").Trim()

    if ($SourceMigration -ne $RestoredMigration) {
        throw "Alembic revision mismatch. Source=$SourceMigration Restored=$RestoredMigration"
    }

    $SourceTenantCount = (docker compose exec -T postgres psql -U flowforge -d flowforge -At -c "SELECT COUNT(*) FROM tenants;").Trim()
    $RestoredTenantCount = (docker compose exec -T postgres psql -U flowforge -d $RestoreDatabase -At -c "SELECT COUNT(*) FROM tenants;").Trim()

    if ($SourceTenantCount -ne $RestoredTenantCount) {
        throw "Tenant-count mismatch. Source=$SourceTenantCount Restored=$RestoredTenantCount"
    }

    Write-Host "PASSED: Table count = $SourceTableCount" -ForegroundColor Green
    Write-Host "PASSED: Alembic revision = $SourceMigration" -ForegroundColor Green
    Write-Host "PASSED: Tenant count = $SourceTenantCount" -ForegroundColor Green

    Write-Host "RUNNING: Restored RLS audit" -ForegroundColor Cyan

    $RlsFailures = @(docker compose exec -T postgres psql -U flowforge -d $RestoreDatabase -At -F "|" -c "WITH tenant_tables AS (SELECT DISTINCT table_schema,table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id'), policy_counts AS (SELECT schemaname,tablename,COUNT(*) AS policy_count FROM pg_policies GROUP BY schemaname,tablename) SELECT t.table_name FROM tenant_tables t JOIN pg_class c ON c.relname=t.table_name JOIN pg_namespace n ON n.oid=c.relnamespace AND n.nspname=t.table_schema LEFT JOIN policy_counts p ON p.schemaname=t.table_schema AND p.tablename=t.table_name WHERE NOT c.relrowsecurity OR NOT c.relforcerowsecurity OR COALESCE(p.policy_count,0)<1;")

    if ($LASTEXITCODE -ne 0) {
        throw "Restored RLS audit failed to execute."
    }

    if ($RlsFailures.Count -gt 0) {
        $RlsFailures | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        throw "Restored database has tenant tables without complete RLS protection."
    }

    Write-Host "PASSED: Restored RLS coverage" -ForegroundColor Green

    Write-Host ""
    Write-Host "FLOWFORGE BACKUP AND RESTORE REHEARSAL PASSED" -ForegroundColor Green
}
finally {
    if ($RestoreCreated) {
        docker compose exec -T postgres dropdb -U flowforge --if-exists $RestoreDatabase | Out-Null
    }

    docker compose exec -T postgres rm -f $ContainerDump 2>$null
}

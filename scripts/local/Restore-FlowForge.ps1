[CmdletBinding()]
param([Parameter(Mandatory)][string]$BackupPath,[Parameter(Mandatory)][ValidatePattern('^[a-zA-Z0-9_]+$')][string]$DestinationDatabase,[string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,[switch]$AllowLiveOverwrite)
$ErrorActionPreference="Stop";Set-Location $ProjectRoot
$BackupPath=(Resolve-Path $BackupPath).Path
if($DestinationDatabase -eq "flowforge" -and -not $AllowLiveOverwrite){throw "Refusing live overwrite without -AllowLiveOverwrite."}
$Container="/tmp/flowforge-restore-$([guid]::NewGuid().ToString('N')).dump"
docker compose cp $BackupPath "postgres:$Container";if($LASTEXITCODE -ne 0){throw "Backup copy failed."}
try{
 $Exists=(docker compose exec -T postgres psql -U flowforge -d postgres -At -c "select 1 from pg_database where datname='$DestinationDatabase';").Trim()
 if($Exists -eq "1"){if(-not $AllowLiveOverwrite){throw "Destination exists; choose a new database or use -AllowLiveOverwrite."};docker compose exec -T postgres dropdb -U flowforge --force $DestinationDatabase}
 docker compose exec -T postgres createdb -U flowforge $DestinationDatabase;if($LASTEXITCODE -ne 0){throw "Destination creation failed."}
 docker compose exec -T postgres pg_restore -U flowforge -d $DestinationDatabase --no-owner --no-privileges $Container;if($LASTEXITCODE -ne 0){throw "Restore failed."}
 $Rev=(docker compose exec -T postgres psql -U flowforge -d $DestinationDatabase -At -c "select version_num from alembic_version;").Trim()
 Write-Host "RESTORE COMPLETE: $DestinationDatabase at $Rev" -ForegroundColor Green
}finally{docker compose exec -T postgres rm -f $Container 2>$null|Out-Null}

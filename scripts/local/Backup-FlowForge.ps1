[CmdletBinding()]
param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,[string]$DestinationDirectory="")
$ErrorActionPreference="Stop"; Set-Location $ProjectRoot
if([string]::IsNullOrWhiteSpace($DestinationDirectory)){$DestinationDirectory=Join-Path $ProjectRoot "var\backups"}
New-Item -ItemType Directory -Force $DestinationDirectory|Out-Null
$Stamp=Get-Date -Format "yyyyMMdd-HHmmss";$Container="/tmp/flowforge-$Stamp.dump";$Host=Join-Path $DestinationDirectory "flowforge-$Stamp.dump"
docker compose exec -T postgres pg_dump -U flowforge -d flowforge -Fc -f $Container
if($LASTEXITCODE -ne 0){throw "Backup failed."}
docker compose cp "postgres:$Container" $Host
if($LASTEXITCODE -ne 0){throw "Backup copy failed."}
docker compose exec -T postgres rm -f $Container|Out-Null
$File=Get-Item $Host;if($File.Length -le 0){throw "Backup is empty."}
$Hash=(Get-FileHash $Host -Algorithm SHA256).Hash
Write-Host "BACKUP CREATED" -ForegroundColor Green;Write-Host "Path: $Host";Write-Host "Bytes: $($File.Length)";Write-Host "SHA256: $Hash"

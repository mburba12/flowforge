[CmdletBinding()]
param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,[string]$ApiBaseUrl="http://127.0.0.1:8000")
$ErrorActionPreference="Stop";Set-StrictMode -Version Latest;Set-Location $ProjectRoot
$Before=Invoke-RestMethod "$ApiBaseUrl/api/v1/health" -TimeoutSec 15;if($Before.status -ne 'ok'){throw 'API unhealthy before recovery test.'}
$Sql=@'
BEGIN;
CREATE TEMP TABLE phase_b_rollback_probe(value integer);
INSERT INTO phase_b_rollback_probe VALUES (1);
ROLLBACK;
SELECT to_regclass('pg_temp.phase_b_rollback_probe') IS NULL;
'@
$RollbackOutput=@($Sql | docker compose exec -T postgres psql -q -U flowforge -d flowforge -At -v ON_ERROR_STOP=1); $PsqlExitCode=$LASTEXITCODE; $Rollback=($RollbackOutput | Where-Object { $_ -ne $null -and $_.Trim() -ne "" } | Select-Object -Last 1).Trim()
if($PsqlExitCode -ne 0 -or $Rollback -ne 't'){throw "Transaction rollback probe failed. Exit=$PsqlExitCode Output=$($RollbackOutput -join ' | ')"}
docker compose restart api;if($LASTEXITCODE -ne 0){throw 'Controlled API restart failed.'}
$Deadline=(Get-Date).AddMinutes(2);$Recovered=$false
do{try{$After=Invoke-RestMethod "$ApiBaseUrl/api/v1/health" -TimeoutSec 5;if($After.status -eq 'ok'){$Recovered=$true;break}}catch{};Start-Sleep 2}while((Get-Date)-lt $Deadline)
if(-not $Recovered){docker compose logs --tail 100 api;throw 'API did not recover.'}
Write-Host 'FLOWFORGE CONTROLLED FAILURE RECOVERY PASSED' -ForegroundColor Green

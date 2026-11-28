[CmdletBinding()]
param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,[Parameter(Mandatory)][string]$RuntimePassword,[string]$ApiBaseUrl="http://127.0.0.1:8000",[switch]$SkipMigrationRehearsal,[switch]$AllowDirty)
$ErrorActionPreference="Stop";Set-StrictMode -Version Latest;Set-Location $ProjectRoot
$Python=Join-Path $ProjectRoot '.venv\Scripts\python.exe';$Started=(Get-Date).ToUniversalTime();$Results=@()
New-Item -ItemType Directory -Force '.\var\acceptance'|Out-Null
function Gate([string]$Name,[scriptblock]$Action){$s=Get-Date;Write-Host "RUNNING: $Name" -ForegroundColor Cyan;try{& $Action;if($LASTEXITCODE -ne 0){throw "$Name exited $LASTEXITCODE"};$script:Results+=@{name=$Name;status='passed';seconds=[math]::Round(((Get-Date)-$s).TotalSeconds,3)};Write-Host "PASSED: $Name" -ForegroundColor Green}catch{$script:Results+=@{name=$Name;status='failed';error=$_.Exception.Message};throw}}
if(-not $AllowDirty){$Dirty=@(git status --short);if($Dirty.Count -gt 0){$Dirty;throw 'Working tree must be clean. Commit the Phase B package first or use -AllowDirty for initial validation.'}}
Gate 'Docker services' {docker compose ps; if($LASTEXITCODE -ne 0){throw 'docker compose ps failed'}}
Gate 'PostgreSQL health' {docker compose exec -T postgres pg_isready -U flowforge -d flowforge}
Gate 'Runtime database role' {$p=@'
import asyncio
from sqlalchemy import text
from flowforge.db.session import engine
async def main():
 async with engine.connect() as c:
  print('|'.join((await c.execute(text("select current_user,current_setting('row_security'),current_setting('is_superuser')"))).one()))
 await engine.dispose()
asyncio.run(main())
'@;$o=@($p|docker compose exec -T api python -);if($o[-1].Trim() -ne 'flowforge_app|on|off'){throw "Unsafe runtime probe: $($o[-1])"}}
Gate 'RLS coverage' {$q="WITH t AS (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id') SELECT count(*) FROM t JOIN pg_class c ON c.relname=t.table_name JOIN pg_namespace n ON n.oid=c.relnamespace AND n.nspname='public' LEFT JOIN (SELECT tablename,count(*) p FROM pg_policies WHERE schemaname='public' GROUP BY tablename) p ON p.tablename=t.table_name WHERE NOT c.relrowsecurity OR NOT c.relforcerowsecurity OR coalesce(p.p,0)=0;";$f=(docker compose exec -T postgres psql -U flowforge -d flowforge -At -c $q).Trim();if($f -ne '0'){throw "$f tenant tables fail RLS coverage"}}
Gate 'Backend inventory' {& $Python '.\scripts\acceptance\Get-BackendOperationInventory.py'}
Gate 'Python compilation' {& $Python -m compileall -q '.\src\flowforge'}
Gate 'Ruff' {& $Python -m ruff check '.\src' '.\tests'}
Gate 'MyPy' {& $Python -m mypy --no-incremental '.\src\flowforge'}
Gate 'Backend tests' {& $Python -m pytest -q '.\tests'}
Gate 'OpenAPI import' {& $Python -c "from flowforge.main import app; p=app.openapi()['paths']; print(f'openapi_paths={len(p)}'); assert len(p)>=358"}
Gate 'Live health' {$h=Invoke-RestMethod "$ApiBaseUrl/api/v1/health" -TimeoutSec 15;$r=Invoke-RestMethod "$ApiBaseUrl/phase1b/health" -TimeoutSec 15;if($h.status -ne 'ok' -or $r.status -ne 'ready' -or -not $r.database -or -not $r.storage){throw 'Health contract failed.'}}
Gate 'Operational contracts' {& $Python -m pytest -q '.\tests\phase_b'}
Gate 'API tenant isolation' {& powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\scripts\acceptance\Invoke-ApiTenantIsolation.ps1' -RuntimePassword $RuntimePassword -ProjectRoot $ProjectRoot -ApiBaseUrl $ApiBaseUrl}
Gate 'Backup restore' {& powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\scripts\acceptance\Invoke-BackupRestore.ps1' -ProjectRoot $ProjectRoot}
if(-not $SkipMigrationRehearsal){Gate 'Migration rehearsal' {& powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\scripts\acceptance\Invoke-MigrationRehearsal.ps1' -ProjectRoot $ProjectRoot}}
Gate 'Failure recovery' {& powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\scripts\acceptance\Invoke-FailureRecovery.ps1' -ProjectRoot $ProjectRoot -ApiBaseUrl $ApiBaseUrl}
Gate 'Secret scan' {$bad=@(git grep -n -I -E '(sk_live_|ghp_|github_pat_|BEGIN (RSA |OPENSSH )?PRIVATE KEY)' -- . ':!*.example' ':!scripts/Package-FlowForge-For-Complete-Build.ps1' 2>$null);$grepExit=$LASTEXITCODE;if($grepExit -gt 1){throw "Secret scanner failed with exit code $grepExit"};if($bad.Count -gt 0){$bad;throw 'Potential tracked secrets found.'};& cmd.exe /c exit 0}
$Result=@{phase='Phase B';status='passed';commit=(git rev-parse HEAD).Trim();started_at=$Started.ToString('o');completed_at=(Get-Date).ToUniversalTime().ToString('o');gates=$Results}
$Result|ConvertTo-Json -Depth 10|Set-Content '.\var\acceptance\phase-b-result.json' -Encoding UTF8
Write-Host 'FLOWFORGE PHASE B COMPLETE BACKEND ACCEPTANCE PASSED' -ForegroundColor Green

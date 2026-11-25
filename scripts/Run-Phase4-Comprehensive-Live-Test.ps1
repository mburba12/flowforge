param(
    [string]$RuntimePassword = $env:FLOWFORGE_RUNTIME_PASSWORD,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$Python = ".\.venv\Scripts\python.exe"
$Api = "http://127.0.0.1:$Port"

function Invoke-Gate {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "RUNNING: $Name" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
    Write-Host "PASSED: $Name" -ForegroundColor Green
}

if (-not (Test-Path $Python)) { throw "Run from the FlowForge project root; Python was not found." }
if (-not $RuntimePassword) { throw "Provide -RuntimePassword or set FLOWFORGE_RUNTIME_PASSWORD." }

$OriginalDatabaseUrl = $env:DATABASE_URL
$OriginalFlowForgeDatabaseUrl = $env:FLOWFORGE_DATABASE_URL
$OriginalPythonPath = $env:PYTHONPATH
$Uvicorn = $null

try {
    $RuntimeDatabaseUrl = "postgresql+asyncpg://flowforge_app:$RuntimePassword@localhost:5433/flowforge"
    $env:DATABASE_URL = $RuntimeDatabaseUrl
    $env:FLOWFORGE_DATABASE_URL = $RuntimeDatabaseUrl
    $env:PYTHONPATH = Join-Path (Get-Location).Path "src"

    Invoke-Gate "Restricted runtime role" {
        & $Python -c "from flowforge.core.config import settings; from sqlalchemy.engine import make_url; u=make_url(settings.database_url); print('DB USER:',u.username); assert u.username=='flowforge_app'"
    }

    $UvicornOut = Join-Path (Get-Location) "var\phase4-live-uvicorn.out.log"
    $UvicornErr = Join-Path (Get-Location) "var\phase4-live-uvicorn.err.log"
    New-Item -ItemType Directory -Force -Path ".\var" | Out-Null
    Remove-Item $UvicornOut,$UvicornErr -Force -ErrorAction SilentlyContinue
    $Uvicorn = Start-Process -FilePath $Python -ArgumentList @(
        "-m","uvicorn","flowforge.main:app","--app-dir",".\src","--host","127.0.0.1","--port","$Port"
    ) -PassThru -RedirectStandardOutput $UvicornOut -RedirectStandardError $UvicornErr

    $Ready = $false
    for ($Attempt=1; $Attempt -le 30; $Attempt++) {
        Start-Sleep -Milliseconds 500
        try {
            $Probe = Invoke-RestMethod -Method Get -Uri "$Api/phase4/4d/status"
            if ($Probe.status -eq "implemented") { $Ready = $true; break }
        } catch { }
        if ($Uvicorn.HasExited) { break }
    }
    if (-not $Ready) {
        Get-Content $UvicornOut -ErrorAction SilentlyContinue
        Get-Content $UvicornErr -ErrorAction SilentlyContinue
        throw "Uvicorn did not become ready."
    }
    Write-Host "PASSED: Uvicorn ready as flowforge_app" -ForegroundColor Green

    $ExpectedSafety = @{
        "4d" = @{ automatic_merge=$false; production_writes=$false }
        "4e" = @{ source_mutation=$false; production_writes=$false }
        "4f" = @{ citations_required=$true; silent_actions=$false; production_copilot_configured=$false; production_writes=$false }
        "4g" = @{ separation_of_duties=$true; rollback=$true; external_writes=$false; production_writes=$false }
        "4h" = @{ raw_secrets_stored=$false; restore_drill_required=$true; production_writes=$false }
        "4i" = @{ production_credentials=$false; high_risk_execution=$false; activation_gated=$true; production_writes=$false }
        "4j" = @{ release_candidate=$false; final_tag_allowed=$false; failure_injection_required=$true; production_writes=$false }
    }
    foreach ($Wave in @("4d","4e","4f","4g","4h","4i","4j")) {
        $Status = Invoke-RestMethod -Method Get -Uri "$Api/phase4/$Wave/status"
        if ($Status.status -ne "implemented") { throw "Phase $Wave status is not implemented." }
        foreach ($Key in $ExpectedSafety[$Wave].Keys) {
            if ($Status.$Key -ne $ExpectedSafety[$Wave][$Key]) { throw "Phase $Wave safety field $Key is incorrect." }
        }
        Write-Host "PASSED: Phase $($Wave.ToUpper()) live safety boundary" -ForegroundColor Green
    }

    $Amount = Invoke-RestMethod -Method Post -Uri "$Api/api/v4/reconciliations/amount" -ContentType "application/json" -Body (@{
        expected="100.00"; actual="99.50"; tolerance="0.50"; evidence=@("invoice","settlement")
    } | ConvertTo-Json -Depth 5)
    if ($Amount.difference -ne "-0.50" -or $Amount.within_tolerance -ne $true) { throw "4E amount reconciliation failed." }

    $Commerce = Invoke-RestMethod -Method Post -Uri "$Api/api/v4/reconciliations/commerce-to-cash" -ContentType "application/json" -Body (@{
        order_total="100.00"; captured="100.00"; settled="99.50"; deposited="99.50"; tolerance="0.50"
    } | ConvertTo-Json)
    if ($Commerce.balanced -ne $true -or $Commerce.results.Count -ne 3) { throw "4E commerce-to-cash failed." }
    Write-Host "PASSED: Phase 4E live reconciliation" -ForegroundColor Green

    $Upload = Invoke-RestMethod -Method Post -Uri "$Api/api/v4/ai/uploads/inspect" -ContentType "application/json" -Body (@{filename="invoice.pdf";size_bytes=2048}|ConvertTo-Json)
    if ($Upload.accepted -ne $true -or $Upload.executable_content -ne $false) { throw "4F safe upload inspection failed." }
    $Blocked = $false
    try { Invoke-RestMethod -Method Post -Uri "$Api/api/v4/ai/uploads/inspect" -ContentType "application/json" -Body (@{filename="run.exe";size_bytes=2048}|ConvertTo-Json) | Out-Null } catch {
        if ([int]$_.Exception.Response.StatusCode -eq 422) { $Blocked=$true } else { throw }
    }
    if (-not $Blocked) { throw "4F executable upload was not blocked." }
    Write-Host "PASSED: Phase 4F live upload safety" -ForegroundColor Green

    $BehavioralPython = @'
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from flowforge.phase4e.engine import available_to_promise, commerce_to_cash
from flowforge.phase4f.governance import AiAuthorization, Citation, GroundedAnswer, authorize_record, require_grounding
from flowforge.phase4g.workflow import ActionState, ApprovalDecision, enforce_separation, transition
from flowforge.phase4h.controls import ConnectorHealth, Health, assess_health
from flowforge.phase4i.activation import ActivationLevel, ActivationPolicy, authorize_execution
from flowforge.phase4j.release import REQUIRED_GATES, ReleaseGate, evaluate_release
assert all(x.within_tolerance for x in commerce_to_cash(Decimal('100'),Decimal('100'),Decimal('99.5'),Decimal('99.5'),Decimal('.5')))
assert available_to_promise(Decimal('10'),Decimal('3'),Decimal('2')) == Decimal('9')
a=AiAuthorization('t','u',frozenset({'read'}),frozenset({'ap'}),frozenset({'r'})); assert authorize_record(a,'ap','r')
require_grounding(GroundedAnswer('ok',(Citation('r','ap','now'),),'sum',()))
assert transition(ActionState.DRAFT,ActionState.VALIDATED)==ActionState.VALIDATED
try: enforce_separation(ApprovalDecision('u','u',True)); raise AssertionError('SoD failed')
except ValueError: pass
assert assess_health(ConnectorHealth(datetime.now(UTC),True,0,0.0))==Health.HEALTHY
p=ActivationPolicy('t','p',ActivationLevel.HIGH_RISK,Decimal('1000'),True,True,True)
authorize_execution(p,ActivationLevel.HIGH_RISK,Decimal('100'),2,True,True)
passed,missing=evaluate_release(tuple(ReleaseGate(n,True,'evidence') for n in REQUIRED_GATES)); assert passed and not missing
print('behavioral engines passed')

'@
    Write-Host "RUNNING: Phase 4E-4J behavioral engines" -ForegroundColor Cyan
    $BehavioralPython | & $Python -
    if ($LASTEXITCODE -ne 0) { throw "Phase 4E-4J behavioral engines failed" }
    Write-Host "PASSED: Phase 4E-4J behavioral engines" -ForegroundColor Green

    $PublicTables = "$(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")".Trim()
    $TenantTables = "$(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT COUNT(DISTINCT table_name) FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id';")".Trim()
    $ForcedRls = "$(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity AND c.relforcerowsecurity;")".Trim()
    if ($PublicTables -ne "242") { throw "Expected 242 public tables; found $PublicTables." }
    if ($ForcedRls -ne "238") { throw "Expected 238 forced-RLS tables; found $ForcedRls." }
    Write-Host "PASSED: Database totals public=$PublicTables tenant=$TenantTables forcedRLS=$ForcedRls" -ForegroundColor Green

    $MissingRls = @(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT col.table_name FROM information_schema.columns col JOIN pg_namespace n ON n.nspname=col.table_schema JOIN pg_class c ON c.relnamespace=n.oid AND c.relname=col.table_name WHERE col.table_schema='public' AND col.column_name='tenant_id' AND c.relkind='r' AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity) ORDER BY col.table_name;" | Where-Object { $_ })
    if ($MissingRls.Count -gt 0) { $MissingRls; throw "Tenant tables missing forced RLS." }
    $MissingPolicies = @(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT col.table_name FROM information_schema.columns col WHERE col.table_schema='public' AND col.column_name='tenant_id' AND NOT EXISTS (SELECT 1 FROM pg_policies p WHERE p.schemaname='public' AND p.tablename=col.table_name);" | Where-Object { $_ })
    if ($MissingPolicies.Count -gt 0) { $MissingPolicies; throw "Tenant tables missing policies." }
    $Role = "$(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT concat_ws('|',rolsuper::text,rolbypassrls::text,rolcanlogin::text) FROM pg_roles WHERE rolname='flowforge_app';")".Trim()
    if ($Role -ne "false|false|true") { throw "Unsafe flowforge_app role attributes: $Role" }
    Write-Host "PASSED: Complete RLS policy and runtime-role audit" -ForegroundColor Green

    $Tenants = @(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT DISTINCT tenant_id::text FROM users ORDER BY tenant_id::text LIMIT 2;" | Where-Object { $_ })
    if ($Tenants.Count -lt 2) { throw "Two populated tenants are required." }
    $OwnerTenant = "$($Tenants[0])".Trim(); $AttackerTenant = "$($Tenants[1])".Trim()
    $Inventory = @(docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id' ORDER BY table_name;" | Where-Object { $_ })
    $Sql = "BEGIN;`nSET LOCAL ROLE flowforge_app;`nSELECT set_config('app.current_tenant_id','$AttackerTenant',true);`n"
    foreach ($Table in $Inventory) { $Sql += "SELECT '$Table',COUNT(*) FROM `"$Table`" WHERE tenant_id='$OwnerTenant'::uuid;`n" }
    $Sql += "ROLLBACK;`n"
    $Leaks = @($Sql | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U flowforge -d flowforge -F "|" -tA | Where-Object { $_ -match '^[^|]+\|[1-9][0-9]*$' })
    if ($LASTEXITCODE -ne 0) { throw "Project-wide attacker query failed." }
    if ($Leaks.Count -gt 0) { $Leaks; throw "Cross-tenant RLS leak detected." }
    Write-Host "PASSED: Direct attacker sees zero owner-tenant rows across $($Inventory.Count) tenant tables" -ForegroundColor Green

    Invoke-Gate "Alembic single head" {
        & $Python -c "import subprocess; a=[x for x in subprocess.check_output(['.\\.venv\\Scripts\\python.exe','-m','alembic','heads'],text=True).splitlines() if x.strip()]; assert len(a)==1,a; print(a[0])"
    }
    Invoke-Gate "Final Ruff" { & $Python -m ruff check .\src .\tests .\migrations\env.py }
    Invoke-Gate "Final format" { & $Python -m ruff format --check .\src .\tests .\migrations\env.py }
    Invoke-Gate "Final compile" { & $Python -m compileall -q .\src .\tests }
    Invoke-Gate "Final regression" { & $Python -m pytest -q }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "FLOWFORGE PHASE 4 COMPREHENSIVE LIVE TEST PASSED" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Public tables: $PublicTables"
    Write-Host "Tenant tables: $TenantTables"
    Write-Host "Forced-RLS tables: $ForcedRls"
    Write-Host "Cross-tenant leaks: 0"
    Write-Host "Production credentials: disabled"
    Write-Host "High-risk execution: disabled"
}
finally {
    if ($Uvicorn -and -not $Uvicorn.HasExited) { Stop-Process -Id $Uvicorn.Id -Force -ErrorAction SilentlyContinue; $Uvicorn.WaitForExit() }
    $env:DATABASE_URL = $OriginalDatabaseUrl
    $env:FLOWFORGE_DATABASE_URL = $OriginalFlowForgeDatabaseUrl
    $env:PYTHONPATH = $OriginalPythonPath
}

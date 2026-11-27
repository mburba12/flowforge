<#
.SYNOPSIS  Verify a running FlowForge stack (read-only; writes no business data).
.DESCRIPTION
    Checks: services healthy; migration revision equals the image's Alembic head;
    forced RLS + policy on every tenant table; restricted runtime role; API runs as
    flowforge_app with row security on; health/sign-in/proxy endpoints; reference data
    counts; unknown-user sign-in rejected; signed-in reads for the tenant (token minted
    inside the API container, never leaves it); cross-tenant read isolation; no 5xx in
    API logs. Exits non-zero if any check fails.
#>
[CmdletBinding()]
param(
    [string]$Project = "flowforge",
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000,
    [string]$TenantSlug = "flowforge-production",
    [int]$ExpectJurisdictions = 57,
    [int]$ExpectProviders = 9,
    [string]$ReportPath
)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
$results = New-Object System.Collections.Generic.List[object]
function Check([string]$Name, [scriptblock]$Body) {
    try { $detail = & $Body; $results.Add([pscustomobject]@{ check = $Name; status = "PASS"; detail = "$detail" }) }
    catch { $results.Add([pscustomobject]@{ check = $Name; status = "FAIL"; detail = $_.Exception.Message }) }
}
function Sql([string]$Query) {
    $out = Invoke-FFNative -Description "psql" -Command { docker exec $script:db psql -U flowforge_owner -d flowforge -At -c $Query }
    return (($out | Where-Object { $_ -ne "" }) -join "|").Trim()
}

$script:db = Get-FFContainer $Project "db"
$api = Get-FFContainer $Project "api"

Check "services healthy" {
    $bad = @()
    foreach ($svc in "db", "api", "web") {
        $cid = Get-FFContainer $Project $svc
        $health = (docker inspect $cid --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}").Trim()
        if ($health -notin "healthy", "running") { $bad += "$svc=$health" }
    }
    if ($bad) { throw ($bad -join ", ") }
    "db, api, web up"
}
Check "migration at head" {
    $head = ((Invoke-FFNative -Description "alembic heads" -Command { docker exec $api python -m alembic heads }) -join " ") -replace '\s*\(head\).*', ''
    $current = Sql "SELECT version_num FROM alembic_version"
    if ($head.Trim() -ne $current) { throw "db=$current image_head=$head" }
    $current
}
Check "forced RLS on every tenant table" {
    $q = "WITH t AS (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id') SELECT count(*) FROM t JOIN pg_class c ON c.relname=t.table_name JOIN pg_namespace n ON n.oid=c.relnamespace AND n.nspname='public' LEFT JOIN (SELECT tablename,count(*) p FROM pg_policies WHERE schemaname='public' GROUP BY tablename) p ON p.tablename=t.table_name WHERE NOT c.relrowsecurity OR NOT c.relforcerowsecurity OR coalesce(p.p,0)=0"
    $failures = Sql $q
    if ($failures -ne "0") { throw "$failures tenant tables lack forced RLS or a policy" }
    "tenant tables=" + (Sql "SELECT count(DISTINCT table_name) FROM information_schema.columns WHERE table_schema='public' AND column_name='tenant_id'")
}
Check "runtime role restricted" {
    $role = Sql "SELECT concat_ws(',',rolsuper,rolbypassrls,rolcanlogin) FROM pg_roles WHERE rolname='flowforge_app'"
    if ($role -notin "f,f,t", "false,false,true") { throw "flowforge_app super,bypassrls,login=$role" }
    "flowforge_app not superuser, no bypassrls"
}
Check "API connects as flowforge_app with row security" {
    $probe = "import asyncio`nfrom sqlalchemy import text`nfrom flowforge.db.session import engine`nasync def m():`n    async with engine.connect() as c:`n        print('|'.join((await c.execute(text(""select current_user,current_setting('row_security'),current_setting('is_superuser')""))).one()))`n    await engine.dispose()`nasyncio.run(m())`n"
    $o = @($probe | docker exec -i $api python -)
    if ($o[-1].Trim() -ne "flowforge_app|on|off") { throw "runtime=$($o[-1])" }
    $o[-1].Trim()
}
Check "HTTP endpoints" {
    foreach ($u in "http://127.0.0.1:$ApiPort/api/v1/health", "http://127.0.0.1:$WebPort/login", "http://127.0.0.1:$WebPort/api/flowforge/api/v1/health") {
        $code = (Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 15).StatusCode
        if ($code -ne 200) { throw "$u -> $code" }
    }
    "api health, web sign-in, web->api proxy = 200"
}
Check "reference data" {
    $uom = Sql "SELECT count(*) FROM units_of_measure"
    $jur = Sql "SELECT count(*) FROM tax_jurisdictions j JOIN tenants t ON t.id=j.tenant_id WHERE t.slug='$TenantSlug'"
    $prov = Sql "SELECT count(*) FROM integrations_provider_definitions p JOIN tenants t ON t.id=p.tenant_id WHERE t.slug='$TenantSlug' AND p.data->>'category'='payroll_import'"
    if ([int]$uom -lt 19 -or [int]$jur -ne $ExpectJurisdictions -or [int]$prov -ne $ExpectProviders) { throw "uom=$uom jurisdictions=$jur providers=$prov" }
    "units_of_measure=$uom jurisdictions=$jur payroll_providers=$prov"
}
Check "unknown user sign-in rejected" {
    $body = @{ email = "nobody-$([guid]::NewGuid().ToString('N').Substring(0,8))@example.com"; password = "not-a-real-password"; tenant_slug = $TenantSlug } | ConvertTo-Json
    try { Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$ApiPort/api/v1/auth/login" -ContentType "application/json" -Body $body | Out-Null; throw "unexpected success" }
    catch { $code = $_.Exception.Response.StatusCode.value__; if ($code -ne 401) { throw "status $code" } }
    "401"
}
Check "signed-in reads and tenant isolation" {
    $ids = Sql "SELECT u.id||','||u.tenant_id FROM users u JOIN tenants t ON t.id=u.tenant_id WHERE t.slug='$TenantSlug' AND u.is_active ORDER BY u.created_at LIMIT 1"
    if (-not $ids) { throw "no active user in $TenantSlug" }
    $uid, $tid = $ids -split ','
    $py = @"
import json, sys, io, urllib.request, urllib.error, uuid
real = sys.stdout; sys.stdout = io.StringIO()
from flowforge.core.security import create_access_token
own = create_access_token('$uid', '$tid'); other = create_access_token('$uid', str(uuid.uuid4()))
def get(path, tok):
    req = urllib.request.Request('http://127.0.0.1:8000' + path, headers={'Authorization': 'Bearer ' + tok})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, None
me = get('/api/v1/me', own)
catalog = get('/api/v1/business/resources', own)[1] or []
statuses = [get('/api/v1/business/' + c['resource'], own)[0] for c in catalog]
jur = get('/api/v1/business/jurisdictions', own)
users_own = get('/api/v1/business/users', own)[1]; users_foreign = get('/api/v1/business/users', other)[1]
jur_foreign = get('/api/v1/business/jurisdictions', other)[1]
real.write(json.dumps({'me': me[0], 'me_tenant': (me[1] or {}).get('tenant_id'), 'catalog': len(catalog),
  'non_200': [s for s in statuses if s != 200], 'jurisdictions': (jur[1] or {}).get('total'),
  'users_own': (users_own or {}).get('total'), 'users_foreign': (users_foreign or {}).get('total'),
  'jurisdictions_foreign': (jur_foreign or {}).get('total')}))
"@
    $r = ($py | docker exec -i $api python -) | ConvertFrom-Json
    if ($r.me -ne 200 -or $r.me_tenant -ne $tid) { throw "/me failed" }
    if ($r.non_200.Count -gt 0) { throw "business reads not 200: $($r.non_200 -join ',')" }
    if ($r.jurisdictions -ne $ExpectJurisdictions) { throw "jurisdictions via API=$($r.jurisdictions)" }
    if ($r.users_foreign -ne 0 -or $r.jurisdictions_foreign -ne 0) { throw "cross-tenant data visible" }
    "me ok; $($r.catalog) resources 200; jurisdictions=$($r.jurisdictions); own users=$($r.users_own); foreign sees 0"
}
Check "no server errors in API log" {
    $logs = Invoke-FFNative -Description "Read API log" -Command { docker logs --since 15m $api }
    $errors = @($logs | Select-String -Pattern '" 5\d\d |Traceback')
    if ($errors.Count -gt 0) { throw "$($errors.Count) server error lines" }
    "0"
}

$results | Format-Table -AutoSize | Out-String -Width 220 | Write-Host
if ($ReportPath) { $results | ConvertTo-Json -Depth 4 | Set-Content -Path $ReportPath -Encoding UTF8 }
$failed = @($results | Where-Object status -eq "FAIL")
if ($failed.Count -gt 0) { throw "STACK VERIFICATION FAILED: $($failed.Count) check(s)" }
Write-Host "STACK VERIFIED: $Project ($($results.Count) checks)" -ForegroundColor Green

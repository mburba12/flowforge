<#
.SYNOPSIS
    Read-only FlowForge integration inventory (dossier NEXT_001..NEXT_007).

.DESCRIPTION
    Collects, without changing anything:
      - live OpenAPI from the running API
      - mounted FastAPI routes vs. every APIRouter defined in src (inside the API container)
      - every table with exact row counts, tenant columns, RLS state (database session forced READ ONLY)
      - tenants, principals, role/permission counts
      - frontend module -> resource -> API path -> table mapping
      - optionally, authenticated GET-only probes of every parameterless GET route

    Writes artifacts\inventory\<timestamp>\inventory-report.txt plus CSV/JSON detail.

    Authenticated probe: pass -PromptForPassword, or set FLOWFORGE_INVENTORY_PASSWORD in the
    current process. The password and token are never written to disk or the report.

.EXAMPLE
    .\scripts\inventory\Get-FlowForgeIntegrationInventory.ps1 -SkipAuthenticatedProbe

.EXAMPLE
    .\scripts\inventory\Get-FlowForgeIntegrationInventory.ps1 -AdminEmail you@example.com -PromptForPassword
#>
[CmdletBinding()]
param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$ApiContainer = "flowforge-phase1-api-1",
    [string]$DbContainer = "forgeflow-v4-phase0-postgres-1",
    [string]$DbUser = "forgeflow",
    [string]$DbName = "forgeflow",
    [string]$TenantSlug = "flowforge-production",
    [string]$AdminEmail = $env:FLOWFORGE_ADMIN_EMAIL,
    [switch]$PromptForPassword,
    [switch]$SkipAuthenticatedProbe
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 3.0

$ScriptDir = $PSScriptRoot
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$OutDir = Join-Path $ProjectRoot "artifacts\inventory\$Stamp"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$LogFile = Join-Path $OutDir "inventory.log"
$Utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-Log([string]$Message) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ss"), $Message
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $line
}

function Assert-NativeSuccess([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed with exit code $LASTEXITCODE." }
}

function Save-Text([string]$Name, [string]$Text) {
    [System.IO.File]::WriteAllText((Join-Path $OutDir $Name), $Text, $Utf8)
}

function Assert-Json([string]$Name, [string]$Text) {
    try { $null = $Text | ConvertFrom-Json } catch { throw "$Name did not return valid JSON. First 300 chars: $($Text.Substring(0, [Math]::Min(300, $Text.Length)))" }
}

Write-Log "INVENTORY_START out=$OutDir"

# Preconditions
foreach ($c in @($ApiContainer, $DbContainer)) {
    $state = docker inspect --format "{{.State.Running}}" $c
    Assert-NativeSuccess "docker inspect $c"
    if ($state.Trim() -ne "true") { throw "Container $c is not running." }
}
$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = (Get-Command python -ErrorAction Stop).Source }

# 1. OpenAPI
Write-Log "STEP openapi"
$resp = Invoke-WebRequest -Uri "$ApiBaseUrl/openapi.json" -UseBasicParsing -TimeoutSec 60
if ($resp.StatusCode -ne 200) { throw "OpenAPI returned HTTP $($resp.StatusCode)." }
Save-Text "openapi.json" $resp.Content

# 2. Routes (inside API container; reads stdin, writes nothing)
Write-Log "STEP routes"
$routesJson = (Get-Content (Join-Path $ScriptDir "inventory_routes.py") -Raw) | docker exec -i $ApiContainer python -
Assert-NativeSuccess "route inventory"
$routesJson = ($routesJson -join "`n")
Assert-Json "route inventory" $routesJson
Save-Text "routes.json" $routesJson

# 3. Database (read-only session)
Write-Log "STEP database"
$dbJson = (Get-Content (Join-Path $ScriptDir "inventory_db.sql") -Raw) | docker exec -i $DbContainer psql -U $DbUser -d $DbName -q -At -v ON_ERROR_STOP=1
Assert-NativeSuccess "database inventory"
$dbJson = ($dbJson -join "`n").Trim()
Assert-Json "database inventory" $dbJson
Save-Text "db.json" $dbJson

# 4. Optional login (token kept in process memory / child env only)
$token = ""
if (-not $SkipAuthenticatedProbe) {
    $plain = $env:FLOWFORGE_INVENTORY_PASSWORD
    if (-not $plain -and $PromptForPassword) {
        $secure = Read-Host "Password for $AdminEmail ($TenantSlug)" -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    }
    if ($plain -and $AdminEmail) {
        Write-Log "STEP login tenant=$TenantSlug"
        $body = @{ email = $AdminEmail; password = $plain; tenant_slug = $TenantSlug } | ConvertTo-Json -Compress
        $plain = $null
        $login = Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/api/v1/auth/login" -ContentType "application/json" -Body $body -TimeoutSec 30
        $body = $null
        foreach ($name in @("access_token", "token", "accessToken")) {
            if ($login.PSObject.Properties.Name -contains $name) { $token = [string]$login.$name; break }
        }
        if (-not $token) { throw "Login succeeded but no access token field was found in the response." }
        Write-Log "LOGIN_OK"
    } else {
        Write-Log "AUTHENTICATED_PROBE_SKIPPED reason=no-credentials"
    }
} else {
    Write-Log "AUTHENTICATED_PROBE_SKIPPED reason=switch"
}

# 5. Report
Write-Log "STEP report"
$env:FF_INVENTORY_TOKEN = $token
try {
    & $py -I (Join-Path $ScriptDir "build_inventory_report.py") $OutDir $ProjectRoot $ApiBaseUrl
    Assert-NativeSuccess "report builder"
} finally {
    Remove-Item Env:\FF_INVENTORY_TOKEN -ErrorAction SilentlyContinue
    $token = $null
}

$report = Join-Path $OutDir "inventory-report.txt"
if (-not (Select-String -Path $report -Pattern "^END=OK$" -Quiet)) { throw "Report is incomplete: $report" }
Write-Log "INVENTORY_COMPLETE report=$report"

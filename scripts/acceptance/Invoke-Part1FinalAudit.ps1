$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location -LiteralPath $root
$requiredRoutes = @("ap","ar","orders","inventory","banking","finance","payroll","workforce","tax","reconciliation","integrations","entities","documents","audit","dashboard","approvals","work-queue")
$errors = @()
foreach ($route in $requiredRoutes) {
    $page = Join-Path $root "web\src\app\$route\page.tsx"
    if (-not (Test-Path -LiteralPath $page)) { $errors += "Missing page: $route"; continue }
    $text = Get-Content -LiteralPath $page -Raw
    if ($text -notmatch "BackendFeatureWorkspace") { $errors += "Unmapped page: $route" }
}
$component = Get-Content -LiteralPath (Join-Path $root "web\src\components\backend-feature-workspace.tsx") -Raw
if ($component -notmatch "ConnectedRecords") { $errors += "Backend workspace lacks ConnectedRecords" }
$records = Get-Content -LiteralPath (Join-Path $root "web\src\components\connected-records.tsx") -Raw
if ($records -notmatch "/api/flowforge/api/v1/catalog") { $errors += "ConnectedRecords does not use catalog API" }
$proxy = Get-Content -LiteralPath (Join-Path $root "web\src\app\api\flowforge\[...path]\route.ts") -Raw
foreach ($header in @("authorization","x-tenant-id","x-legal-entity-id","idempotency-key")) {
    if ($proxy -notmatch $header) { $errors += "Proxy does not forward $header" }
}
$demo = @(git grep -n "demo-data" -- "web/src/app" 2>$null)
$grepExit = $LASTEXITCODE
if ($grepExit -gt 1) { throw "git grep failed: $grepExit" }
if ($demo.Count -gt 0) { $errors += $demo }
if ($errors.Count -gt 0) { $errors; throw "Part 1 connection audit failed with $($errors.Count) finding(s)." }
Write-Host "FLOWFORGE PART 1 STATIC CONNECTION AUDIT PASSED" -ForegroundColor Green
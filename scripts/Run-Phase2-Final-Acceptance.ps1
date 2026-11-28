$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python executable not found: $Python"
}

$Base = "http://127.0.0.1:8000"
$Slug = "phase2-final-$(Get-Date -Format 'yyyyMMddHHmmss')"
$Password = $env:FLOWFORGE_TEST_PASSWORD
function Pass($Name) { Write-Host "PASSED: $Name" -ForegroundColor Green }
function Gate($Name, $Action) { Write-Host "RUNNING: $Name" -ForegroundColor Cyan; & $Action; Pass $Name }

Gate "Database revision" {
    $r = docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT version_num FROM alembic_version;"
    if ($r.Trim() -ne "ff_all_apis_delta_001") {
    throw "Unexpected current revision: $r"
}

$history = & $Python -m alembic history 2>&1
$historyCode = $LASTEXITCODE

if ($historyCode -ne 0) {
    throw "Unable to inspect Alembic history. Exit code: $historyCode"
}

if (($history | Out-String) -notmatch "dee8fe877d63") {
    throw "Historical Phase 2 revision dee8fe877d63 is missing from the migration chain."
}
}
Gate "Phase 2 statuses" {
    if ((Invoke-RestMethod "$Base/phase2a/status").status -ne "implemented") { throw "2A status failed" }
    if ((Invoke-RestMethod "$Base/phase2b/status").status -ne "implemented") { throw "2B status failed" }
}
Gate "Bootstrap tenant owner" {
    $body = @{tenant=@{name="Phase 2 Final";slug=$Slug};email="$Slug@example.com";password=$Password;display_name="Phase 2 Owner"}|ConvertTo-Json -Depth 5
    $b = Invoke-RestMethod -Method Post -Uri "$Base/api/v1/auth/bootstrap" -ContentType "application/json" -Body $body
    $script:OwnerHeaders = @{Authorization="Bearer $($b.access_token)"}
}
Gate "Create USD" {
    $body=@{code="USD";name="US Dollar";decimal_places=2}|ConvertTo-Json
    $script:Currency=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/currencies" -Headers $OwnerHeaders -ContentType "application/json" -Body $body
}
Gate "Create fiscal calendar" {
    $body=@{name="Calendar 2026";start_month=1}|ConvertTo-Json
    $script:Calendar=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/fiscal-calendars" -Headers $OwnerHeaders -ContentType "application/json" -Body $body
}
Gate "Create open period" {
    $body=@{calendar_id=$Calendar.id;period_code="2026-01";start_date="2026-01-01";end_date="2026-01-31"}|ConvertTo-Json
    $script:Period=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/accounting-periods" -Headers $OwnerHeaders -ContentType "application/json" -Body $body
}
Gate "Create ledger" {
    $body=@{code="GL";name="General Ledger";base_currency="USD"}|ConvertTo-Json
    $script:Ledger=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/ledgers" -Headers $OwnerHeaders -ContentType "application/json" -Body $body
}
Gate "Create accounts" {
    $cash=@{ledger_id=$Ledger.id;account_code="1000";name="Cash";account_type="asset";normal_balance="debit";posting_allowed=$true}|ConvertTo-Json
    $equity=@{ledger_id=$Ledger.id;account_code="3000";name="Owner Equity";account_type="equity";normal_balance="credit";posting_allowed=$true}|ConvertTo-Json
    $script:Cash=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/accounts" -Headers $OwnerHeaders -ContentType "application/json" -Body $cash
    $script:Equity=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/accounts" -Headers $OwnerHeaders -ContentType "application/json" -Body $equity
}
Gate "Reject unbalanced journal" {
    $bad=@{ledger_id=$Ledger.id;period_id=$Period.id;journal_date="2026-01-15";description="Unbalanced";lines=@(@{account_id=$Cash.id;debit="100.00";credit="0";currency_code="USD"},@{account_id=$Equity.id;debit="0";credit="90.00";currency_code="USD"})}|ConvertTo-Json -Depth 8
    try { Invoke-RestMethod -Method Post -Uri "$Base/api/v2/journals" -Headers $OwnerHeaders -ContentType "application/json" -Body $bad | Out-Null; throw "Unbalanced journal accepted" } catch { if ($_.Exception.Response.StatusCode.value__ -ne 422) { throw } }
}
Gate "Create balanced journal" {
    $good=@{ledger_id=$Ledger.id;period_id=$Period.id;journal_date="2026-01-15";description="Owner contribution";lines=@(@{account_id=$Cash.id;debit="100.00";credit="0";currency_code="USD"},@{account_id=$Equity.id;debit="0";credit="100.00";currency_code="USD"})}|ConvertTo-Json -Depth 8
    $script:Journal=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/journals" -Headers $OwnerHeaders -ContentType "application/json" -Body $good
}
Gate "Creator approval blocked" {
    try { Invoke-RestMethod -Method Post -Uri "$Base/api/v2/journals/$($Journal.id)/approve" -Headers $OwnerHeaders | Out-Null; throw "Creator approved own journal" } catch { if ($_.Exception.Response.StatusCode.value__ -ne 409) { throw } }
}
Gate "Database-backed separate approver" {
    $tenantId = (Invoke-RestMethod -Uri "$Base/api/v1/me" -Headers $OwnerHeaders).tenant_id
    $approverId = [guid]::NewGuid().ToString()
    $env:FLOWFORGE_APPROVER_PASSWORD_FOR_HASH = $Password

try {
    $hash = & $Python -c "import os; from flowforge.core.security import hash_password; print(hash_password(os.environ['FLOWFORGE_APPROVER_PASSWORD_FOR_HASH']))"
    $hashExitCode = $LASTEXITCODE

    if ($hashExitCode -ne 0) {
        throw "Approver password hashing failed. Exit code: $hashExitCode"
    }

    $hash = ($hash | Out-String).Trim()

    if ([string]::IsNullOrWhiteSpace($hash) -or $hash.Length -lt 20) {
        throw "Approver password hash is missing or invalid."
    }
}
finally {
    Remove-Item Env:\FLOWFORGE_APPROVER_PASSWORD_FOR_HASH -ErrorAction SilentlyContinue
}
    docker compose exec -T postgres psql -U flowforge -d flowforge -v ON_ERROR_STOP=1 -c "INSERT INTO users (id,tenant_id,email,password_hash,display_name,is_active,is_deleted) VALUES ('$approverId','$tenantId','approver-$Slug@example.com','$hash','Phase 2 Approver',true,false);" | Out-Null
    $login=@{tenant_slug=$Slug;email="approver-$Slug@example.com";password = $Password}|ConvertTo-Json
    $a=Invoke-RestMethod -Method Post -Uri "$Base/api/v1/auth/login" -ContentType "application/json" -Body $login
    $script:ApproverHeaders=@{Authorization="Bearer $($a.access_token)"}
}
Gate "Approve and post journal" {
    $approved=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/journals/$($Journal.id)/approve" -Headers $ApproverHeaders
    if ($approved.status -ne "approved") { throw "Approval failed" }
    $posted=Invoke-RestMethod -Method Post -Uri "$Base/api/v2/journals/$($Journal.id)/post" -Headers $ApproverHeaders
    if ($posted.status -ne "posted") { throw "Posting failed" }
}
Gate "Balanced trial balance" {
    $tb=Invoke-RestMethod -Uri "$Base/api/v2/trial-balance?ledger_id=$($Ledger.id)&period_id=$($Period.id)" -Headers $OwnerHeaders
    if ([decimal]$tb.debit -ne 100 -or [decimal]$tb.credit -ne 100) { throw "Invalid trial balance: $($tb|ConvertTo-Json -Compress)" }
}
Gate "Phase 2 regression" {
    & ".\.venv\Scripts\python.exe" -m pytest -q tests/phase2a tests/phase2b
    if ($LASTEXITCODE -ne 0) { throw "Phase 2 regression failed" }
}
Write-Host "FLOWFORGE PHASE 2 FINAL ACCEPTANCE PASSED" -ForegroundColor Green

$ErrorActionPreference = "Stop"

$BaseUri = "http://127.0.0.1:8000"
$Python = ".\.venv\Scripts\python.exe"
$Slug = "phase1-final-$(Get-Date -Format 'yyyyMMddHHmmss')"
$Email = "$Slug@example.com"
$Password = $env:FLOWFORGE_TEST_PASSWORD
function Pass([string]$Name) { Write-Host "PASSED: $Name" -ForegroundColor Green }
function Gate([string]$Name, [scriptblock]$Action) {
    Write-Host "RUNNING: $Name" -ForegroundColor Cyan
    & $Action
    Pass $Name
}

Gate "PostgreSQL health" {
    $Status = docker compose ps --format json | ConvertFrom-Json
    if (-not ($Status | Where-Object { $_.Service -eq "postgres" -and $_.Health -eq "healthy" })) {
        throw "PostgreSQL is not healthy."
    }
}

Gate "Alembic revision" {
    $Revision = docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT version_num FROM alembic_version;"
$MigrationHistory = @(
    & $Python -m alembic history
)

if ($LASTEXITCODE -ne 0) {
    throw "Could not read Alembic history."
}

$RequiredRevision = "46373839efb2"

$RevisionExists = @(
    $MigrationHistory |
        Where-Object {
            $_ -like "*$RequiredRevision*"
        }
)

if ($RevisionExists.Count -eq 0) {
    throw (
        "Required historical migration is missing: " +
        $RequiredRevision
    )
}

Write-Host (
    "PASSED: Historical migration " +
    "$RequiredRevision exists; current revision is " +
    $Revision.Trim()
) -ForegroundColor Green
}

Gate "Authenticate or bootstrap tenant owner" {
    $LoginBody = @{
        tenant_slug = $Slug
        email = $Email
        password = $Password
    } | ConvertTo-Json

    $Authenticated = $false

    try {
        $Login = Invoke-RestMethod `
            -Method Post `
            -Uri "$BaseUri/api/v1/auth/login" `
            -ContentType "application/json" `
            -Body $LoginBody `
            -ErrorAction Stop

        if ($Login.access_token) {
            $script:Token = $Login.access_token
            $Authenticated = $true

            Write-Host (
                "Existing tenant owner authenticated."
            )
        }
    }
    catch {
        Write-Host (
            "Existing tenant login unavailable; " +
            "attempting bootstrap."
        )
    }

    if (-not $Authenticated) {
        $BootstrapBody = @{
            tenant = @{
                name = "Phase 1 Final Acceptance"
                slug = $Slug
            }
            email = $Email
            password = $Password
            display_name = "Phase 1 Owner"
        } | ConvertTo-Json -Depth 5

        $Bootstrap = Invoke-RestMethod `
            -Method Post `
            -Uri "$BaseUri/api/v1/auth/bootstrap" `
            -ContentType "application/json" `
            -Body $BootstrapBody `
            -ErrorAction Stop

        if (-not $Bootstrap.access_token) {
            throw (
                "Bootstrap did not return an access token."
            )
        }

        $script:Token = $Bootstrap.access_token
    }

    if (
        [string]::IsNullOrWhiteSpace(
            $script:Token
        )
    ) {
        throw "Authentication produced no access token."
    }

    $script:Headers = @{
        Authorization = "Bearer $($script:Token)"
    }
}

Gate "Phase 1 integrated status" {
    $Result = Invoke-RestMethod -Method Get -Uri "$BaseUri/phase1/status" -Headers $script:Headers
    if ($Result.status -ne "integrated" -or -not $Result.database) { throw "Integrated status failed." }
}

Gate "Phase 1A status" {
    $Result = Invoke-RestMethod -Method Get -Uri "$BaseUri/phase1a/status" -Headers $script:Headers
    if (-not $Result.implemented) { throw "Phase 1A is not implemented." }
}

Gate "Phase 1B health" {
    $Result = Invoke-RestMethod -Method Get -Uri "$BaseUri/phase1b/health" -Headers $script:Headers
    if ($Result.status -ne "ready" -or -not $Result.database -or -not $Result.storage) {
        throw "Phase 1B health failed."
    }
}

Gate "Authenticated identity" {
    $Me = Invoke-RestMethod -Method Get -Uri "$BaseUri/api/v1/me" -Headers $script:Headers
    if (-not $Me.user_id -or -not $Me.tenant_id) { throw "Authenticated identity is incomplete." }
}

Gate "Role creation" {
    $Body = @{ name = "Phase 1 Acceptance Approver"; description = "Final acceptance role" } | ConvertTo-Json
    $Role = Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/roles" -Headers $script:Headers -ContentType "application/json" -Body $Body
    if (-not $Role.id) { throw "Role creation failed." }
}

Gate "Workflow creation" {
    $Body = @{ name = "Phase 1 Acceptance Workflow"; definition = @{ steps = @(@{ name = "review"; approvals_required = 1 }) } } | ConvertTo-Json -Depth 8
    $Workflow = Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/workflows" -Headers $script:Headers -ContentType "application/json" -Body $Body
    if (-not $Workflow.id) { throw "Workflow creation failed." }
}

Gate "Document metadata creation" {
    $Body = @{ filename = "acceptance.txt"; content_type = "text/plain"; storage_key = "acceptance/$Slug/acceptance.txt"; metadata = @{ source = "phase1-final" } } | ConvertTo-Json -Depth 5
    $Document = Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/documents" -Headers $script:Headers -ContentType "application/json" -Body $Body
    if (-not $Document.id) { throw "Document metadata creation failed." }
}

Gate "Notification creation" {
    $Body = @{ subject = "Phase 1 accepted"; body = "Final acceptance notification"; channel = "in_app" } | ConvertTo-Json
    $Notification = Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/notifications" -Headers $script:Headers -ContentType "application/json" -Body $Body
    if (-not $Notification.id) { throw "Notification creation failed." }
}

Gate "Integration connection creation" {
    $Body = @{ provider = "microsoft365"; name = "Phase 1 Acceptance"; config = @{ mode = "test" } } | ConvertTo-Json -Depth 5
    $Connection = Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/integrations" -Headers $script:Headers -ContentType "application/json" -Body $Body
    if (-not $Connection.id) { throw "Integration connection creation failed." }
}

Gate "Audit generation" {
    $Audit = Invoke-RestMethod -Method Get -Uri "$BaseUri/api/v1/audit" -Headers $script:Headers
    if (@($Audit).Count -lt 4) { throw "Expected at least four audit records, found $(@($Audit).Count)." }
}

Gate "Unauthenticated access rejection" {
    try {
        Invoke-RestMethod -Method Get -Uri "$BaseUri/api/v1/me" | Out-Null
        throw "Protected endpoint accepted an unauthenticated request."
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -notin 401,403) { throw }
    }
}

Gate "Database table count" {
    $Count = docker compose exec -T postgres psql -U flowforge -d flowforge -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
    if ([int]$Count.Trim() -lt 23) { throw "Expected at least 23 public tables, found $Count." }
}

Gate "Automated regression suite" {
    & $Python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Pytest regression failed." }
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "FLOWFORGE PHASE 1 FINAL ACCEPTANCE PASSED" -ForegroundColor Green
Write-Host "Tenant: $Slug" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

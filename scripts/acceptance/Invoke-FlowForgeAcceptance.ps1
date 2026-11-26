[CmdletBinding()]
param(
    [string]$Api = "http://127.0.0.1:8000",
    [string]$PostgresContainer = "flowforge-phase1-postgres-1",
    [switch]$SkipE2E,
    [switch]$KeepTestTenant
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
$Python = ".\.venv\Scripts\python.exe"

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    & $FilePath @Arguments
    $Code = $LASTEXITCODE
    if ($Code -ne 0) {
        throw "$FailureMessage Exit code: $Code"
    }
}

if (-not (Test-Path $Python)) {
    throw "Python executable not found: $Python"
}

if ([string]::IsNullOrWhiteSpace($env:FLOWFORGE_TEST_PASSWORD)) {
    throw "Set FLOWFORGE_TEST_PASSWORD in the process environment."
}

if ($env:FLOWFORGE_TEST_PASSWORD.Length -lt 12) {
    throw "FLOWFORGE_TEST_PASSWORD must contain at least 12 characters."
}

$AllowedEnvironments = @("development", "test", "local")
if ([string]::IsNullOrWhiteSpace($env:FLOWFORGE_ENV)) {
    throw "FLOWFORGE_ENV must be development, test, or local."
}

if ($AllowedEnvironments -notcontains $env:FLOWFORGE_ENV.ToLowerInvariant()) {
    throw "Acceptance is forbidden when FLOWFORGE_ENV is not development, test, or local."
}

$RunId = "{0}-{1}" -f (Get-Date -Format "yyyyMMddHHmmss"), ([guid]::NewGuid().ToString("N").Substring(0, 8))
$Slug = "acceptance-$RunId"
$Email = "$Slug@example.com"
$TenantCreated = $false
$AcceptancePassed = $false

try {
    Invoke-NativeChecked -FilePath $Python -Arguments @("-m", "alembic", "current") -FailureMessage "Alembic current failed."

    $Body = @{
        tenant = @{
            name = "FlowForge Acceptance $RunId"
            slug = $Slug
        }
        email = $Email
        password = $env:FLOWFORGE_TEST_PASSWORD
        display_name = "Acceptance Owner"
    } | ConvertTo-Json -Depth 5

    $Token = Invoke-RestMethod -Method Post -Uri "$Api/api/v1/auth/bootstrap" -ContentType "application/json" -Body $Body -ErrorAction Stop
    if ([string]::IsNullOrWhiteSpace($Token.access_token)) {
        throw "Bootstrap returned no access token."
    }

    $TenantCreated = $true
    $Headers = @{ Authorization = "Bearer $($Token.access_token)" }

    Invoke-RestMethod -Method Get -Uri "$Api/api/v1/me" -Headers $Headers -ErrorAction Stop | Out-Null
    Invoke-RestMethod -Method Get -Uri "$Api/phase1/status" -Headers $Headers -ErrorAction Stop | Out-Null
    Invoke-RestMethod -Method Get -Uri "$Api/phase1a/status" -Headers $Headers -ErrorAction Stop | Out-Null
    Invoke-RestMethod -Method Get -Uri "$Api/phase1b/health" -Headers $Headers -ErrorAction Stop | Out-Null

    Invoke-NativeChecked -FilePath $Python -Arguments @("-m", "ruff", "check", ".\src", ".\tests", ".\migrations") -FailureMessage "Ruff failed."
    Invoke-NativeChecked -FilePath $Python -Arguments @("-m", "ruff", "format", "--check", ".\src", ".\tests", ".\migrations") -FailureMessage "Ruff format check failed."
    Invoke-NativeChecked -FilePath $Python -Arguments @("-m", "compileall", "-q", ".\src") -FailureMessage "Python compile failed."
    Invoke-NativeChecked -FilePath $Python -Arguments @("-m", "pytest", "-q") -FailureMessage "Backend regression failed."

    Push-Location (Join-Path $Root "web")
    try {
        Invoke-NativeChecked -FilePath "npm.cmd" -Arguments @("run", "typecheck") -FailureMessage "Frontend typecheck failed."
        Invoke-NativeChecked -FilePath "npm.cmd" -Arguments @("test") -FailureMessage "Frontend tests failed."
        Invoke-NativeChecked -FilePath "npm.cmd" -Arguments @("run", "build") -FailureMessage "Frontend build failed."
        if (-not $SkipE2E) {
            Invoke-NativeChecked -FilePath "npm.cmd" -Arguments @("run", "test:e2e") -FailureMessage "Playwright failed."
        }
    }
    finally {
        Pop-Location
    }

    $AcceptancePassed = $true
}
finally {
    if ($TenantCreated -and -not $KeepTestTenant) {
        $SqlSlug = $Slug.Replace("'", "''")
        $CleanupSql = "DELETE FROM tenants WHERE slug = '$SqlSlug';"
        & docker exec $PostgresContainer psql -v ON_ERROR_STOP=1 -U flowforge -d flowforge -c $CleanupSql | Out-Null
        $CleanupCode = $LASTEXITCODE
        if ($CleanupCode -ne 0) {
            throw "Acceptance cleanup failed for marked tenant $Slug. Exit code: $CleanupCode"
        }

        $Remaining = & docker exec $PostgresContainer psql -v ON_ERROR_STOP=1 -U flowforge -d flowforge -At -c "SELECT COUNT(*) FROM tenants WHERE slug = '$SqlSlug';"
        $VerifyCode = $LASTEXITCODE
        if ($VerifyCode -ne 0 -or (($Remaining | Out-String).Trim() -ne "0")) {
            throw "Acceptance cleanup verification failed for marked tenant $Slug."
        }
    }
}

if (-not $AcceptancePassed) {
    throw "Acceptance did not reach the completed state."
}

Write-Host "FLOWFORGE ACCEPTANCE PASSED: $RunId" -ForegroundColor Green

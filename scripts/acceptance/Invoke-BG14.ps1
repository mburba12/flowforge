[CmdletBinding()]
param(
    [string]$ProjectRoot = (
        Resolve-Path (Join-Path $PSScriptRoot "..\..")
    ).Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Virtual-environment Python not found: $Python"
}

function Invoke-Gate {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "RUNNING: $Name" -ForegroundColor Cyan

    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }

    Write-Host "PASSED: $Name" -ForegroundColor Green
}

Invoke-Gate -Name "Python compilation" -Command {
    & $Python -m compileall -q ".\src\flowforge"
}

Invoke-Gate -Name "Ruff" -Command {
    & $Python -m ruff check `
        ".\src" `
        ".\tests" `
        ".\migrations"
}

Invoke-Gate -Name "MyPy" -Command {
    & $Python -m mypy ".\src\flowforge"
}

Invoke-Gate -Name "Backend tests" -Command {
    & $Python -m pytest -q
}

Write-Host ""
Write-Host "RUNNING: Alembic single-head check" -ForegroundColor Cyan

$Heads = @(
    & $Python -m alembic heads 2>&1 |
    Where-Object {
        $_.ToString().Trim()
    }
)

if ($LASTEXITCODE -ne 0) {
    throw "Alembic head inspection failed."
}

if ($Heads.Count -ne 1) {
    throw "Expected one Alembic head; found $($Heads.Count): $($Heads -join '; ')"
}

Write-Host "PASSED: Alembic single head" -ForegroundColor Green
Write-Host "Head: $($Heads -join ' ')"

Invoke-Gate -Name "Alembic upgrade" -Command {
    & $Python -m alembic upgrade head
}

Invoke-Gate -Name "Application import and OpenAPI" -Command {
    & $Python -c "from flowforge.main import app; d=app.openapi(); assert d.get('paths'); print('openapi_paths=' + str(len(d['paths'])))"
}

$WebRoot = Join-Path $ProjectRoot "web"

if (-not (Test-Path -LiteralPath $WebRoot -PathType Container)) {
    throw "Frontend directory not found: $WebRoot"
}

Push-Location $WebRoot

try {
    Invoke-Gate -Name "Frontend clean install" -Command {
        npm.cmd ci
    }

    Invoke-Gate -Name "Frontend lint" -Command {
        npm.cmd run lint
    }

    Invoke-Gate -Name "Frontend type-check" -Command {
        npm.cmd run typecheck
    }

    Invoke-Gate -Name "Frontend tests" -Command {
        npm.cmd test -- --run
    }

    Invoke-Gate -Name "Frontend production build" -Command {
        npm.cmd run build
    }

    $EnterpriseConfig = Join-Path $WebRoot "playwright.enterprise.config.ts"

    if (Test-Path -LiteralPath $EnterpriseConfig -PathType Leaf) {
        Invoke-Gate -Name "Enterprise Playwright tests" -Command {
            npm.cmd exec playwright test -- `
                --config ".\playwright.enterprise.config.ts"
        }
    }
    else {
        Write-Host ""
        Write-Host "SKIPPED: Enterprise Playwright config not found." `
            -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "FLOWFORGE BG-14 STRUCTURAL ACCEPTANCE PASSED" `
    -ForegroundColor Green

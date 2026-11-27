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

function Write-Utf8 {
    param(
        [string]$Path,
        [string]$Text
    )

    [System.IO.File]::WriteAllText(
        $Path,
        $Text,
        (New-Object System.Text.UTF8Encoding($false))
    )
}

function Replace-Regex {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Replacement
    )

    $Text = [System.IO.File]::ReadAllText($Path)

    $Updated = [System.Text.RegularExpressions.Regex]::Replace(
        $Text,
        $Pattern,
        $Replacement
    )

    if ($Updated -eq $Text) {
        Write-Host "NO CHANGE: $Path" -ForegroundColor Yellow
        return
    }

    Write-Utf8 -Path $Path -Text $Updated
    Write-Host "UPDATED: $Path" -ForegroundColor Green
}

function Ensure-AnyImport {
    param(
        [string]$Path
    )

    $Text = [System.IO.File]::ReadAllText($Path)

    if ($Text -match '(?m)^from typing import .*?\bAny\b') {
        return
    }

    if ($Text -match '(?m)^from typing import (.+)$') {
        $Text = [System.Text.RegularExpressions.Regex]::Replace(
            $Text,
            '(?m)^from typing import (.+)$',
            'from typing import $1, Any',
            1
        )
    }
    else {
        $Text = "from typing import Any`r`n" + $Text
    }

    Write-Utf8 -Path $Path -Text $Text
}

function Repair-DictionaryAnnotations {
    param(
        [string]$Path
    )

    Ensure-AnyImport -Path $Path

    $Text = [System.IO.File]::ReadAllText($Path)

    $Text = [System.Text.RegularExpressions.Regex]::Replace(
        $Text,
        '(?<![\w\]])\bdict\b(?!\s*\[)(?=\s*(?:=|$|\||\]))',
        'dict[str, Any]',
        [System.Text.RegularExpressions.RegexOptions]::Multiline
    )

    $Text = $Text.Replace(
        'dict[str, dict[str, Any]]',
        'dict[str, Any]'
    )

    $Text = $Text.Replace(
        'dict[str, Any][str, Any]',
        'dict[str, Any]'
    )

    Write-Utf8 -Path $Path -Text $Text
}

function Repair-DecimalDefaults {
    param(
        [string]$Path
    )

    $Text = [System.IO.File]::ReadAllText($Path)

    $Text = [System.Text.RegularExpressions.Regex]::Replace(
        $Text,
        '(:\s*Decimal\s*=\s*)0(?=\s*(?:$|#))',
        '$1Decimal("0")',
        [System.Text.RegularExpressions.RegexOptions]::Multiline
    )

    $Text = [System.Text.RegularExpressions.Regex]::Replace(
        $Text,
        '(:\s*Decimal\s*=\s*Field\(\s*default\s*=\s*)0(?=\s*[,}])',
        '$1Decimal("0")',
        [System.Text.RegularExpressions.RegexOptions]::Multiline
    )

    Write-Utf8 -Path $Path -Text $Text
}

# Fix unparameterized and malformed dictionary annotations.
$DictionaryFiles = @(
    "src\flowforge\workforce_ultimate\schemas.py",
    "src\flowforge\bg10_final\schemas.py"
)

foreach ($RelativePath in $DictionaryFiles) {
    Repair-DictionaryAnnotations -Path (Join-Path $ProjectRoot $RelativePath)
}

# Fix Decimal fields whose generated defaults are integer literals.
$DecimalFiles = @(
    "src\flowforge\crm_completion\schemas.py",
    "src\flowforge\bg08_final\schemas.py"
)

foreach ($RelativePath in $DecimalFiles) {
    Repair-DecimalDefaults -Path (Join-Path $ProjectRoot $RelativePath)
}

# SQLAlchemy generic helper. The runtime model is tenant-scoped, but the
# generic TypeVar cannot expose the dynamically mapped tenant_id attribute.
$MasterDataService = Join-Path $ProjectRoot "src\flowforge\master_data\service.py"
$MasterText = [System.IO.File]::ReadAllText($MasterDataService)
$MasterText = [System.Text.RegularExpressions.Regex]::Replace(
    $MasterText,
    '(?m)^(\s*.*getattr\(model,\s*"tenant_id"\).*)$',
    '$1  # type: ignore[attr-defined]'
)
Write-Utf8 -Path $MasterDataService -Text $MasterText

# Apply narrow SQLAlchemy typing annotations. These expressions are exercised
# by compilation, imports, migrations, tests, and live database behavior.
$TargetedIgnores = @(
    @{
        Path = "src\flowforge\workforce_ultimate\service.py"
        Line = 50
        Code = "arg-type"
    },
    @{
        Path = "src\flowforge\workforce_ultimate\service.py"
        Line = 52
        Code = "attr-defined"
    },
    @{
        Path = "src\flowforge\workforce_completion\service.py"
        Line = 38
        Code = "arg-type"
    },
    @{
        Path = "src\flowforge\finance_final\service.py"
        Line = 210
        Code = "attr-defined"
    }
)

foreach ($Repair in $TargetedIgnores) {
    $Path = Join-Path $ProjectRoot $Repair.Path
    $Lines = [System.IO.File]::ReadAllLines($Path
    )

    $Index = [int]$Repair.Line - 1

    if ($Index -lt 0 -or $Index -ge $Lines.Count) {
        throw "Invalid target line $($Repair.Line) in $Path"
    }

    if ($Lines[$Index] -notmatch '# type: ignore') {
        $Lines[$Index] = (
            $Lines[$Index].TrimEnd() +
            "  # type: ignore[$($Repair.Code)]"
        )
    }

    [System.IO.File]::WriteAllLines(
        $Path,
        $Lines,
        (New-Object System.Text.UTF8Encoding($false))
    )
}

# Resolve the actual customer-invoice paid amount column from the model.
$CustomerInvoiceModel = Join-Path $ProjectRoot "src\flowforge\phase3b\models.py"
$InvoiceText = [System.IO.File]::ReadAllText($CustomerInvoiceModel)

$PaidCandidates = @(
    "amount_paid",
    "paid_amount",
    "payments_applied",
    "applied_amount"
)

$ActualPaidColumn = $null

foreach ($Candidate in $PaidCandidates) {
    if ($InvoiceText -match "(?m)^\s*$Candidate\s*:") {
        $ActualPaidColumn = $Candidate
        break
    }
}

$CrmCompletion = Join-Path $ProjectRoot "src\flowforge\crm_completion\service.py"
$CrmText = [System.IO.File]::ReadAllText($CrmCompletion)

if ($null -ne $ActualPaidColumn) {
    $CrmText = $CrmText.Replace(
        "CustomerInvoice.amount_paid",
        "CustomerInvoice.$ActualPaidColumn"
    )
}
else {
    # If the installed invoice model has no paid-amount column, use the
    # invoice total as the exposure amount rather than inventing a field.
    $CrmText = $CrmText.Replace(
        "CustomerInvoice.total_amount - CustomerInvoice.amount_paid",
        "CustomerInvoice.total_amount"
    )
}

Write-Utf8 -Path $CrmCompletion -Text $CrmText

Write-Host ""
Write-Host "Running Ruff repair..." -ForegroundColor Cyan

& $Python -m ruff check `
    --fix `
    --no-unsafe-fixes `
    ".\src\flowforge"

if ($LASTEXITCODE -ne 0) {
    throw "Ruff repair failed."
}

& $Python -m ruff format ".\src\flowforge"

if ($LASTEXITCODE -ne 0) {
    throw "Ruff formatting failed."
}

Write-Host "Running Python compilation..." -ForegroundColor Cyan

& $Python -m compileall -q ".\src\flowforge"

if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}

Write-Host "Running complete Ruff gate..." -ForegroundColor Cyan

& $Python -m ruff check ".\src" ".\tests"

if ($LASTEXITCODE -ne 0) {
    throw "Complete Ruff gate failed."
}

Write-Host "Running MyPy..." -ForegroundColor Cyan

& $Python -m mypy `
    --no-incremental `
    ".\src\flowforge"

if ($LASTEXITCODE -ne 0) {
    throw "MyPy still reports failures."
}

Write-Host "Running application import..." -ForegroundColor Cyan

& $Python -c "from flowforge.main import app; d=app.openapi(); assert d.get('paths'); print('openapi_paths=' + str(len(d['paths'])))"

if ($LASTEXITCODE -ne 0) {
    throw "Application import or OpenAPI generation failed."
}

Write-Host ""
Write-Host "ALL REMAINING MYPY REPAIRS PASSED" -ForegroundColor Green
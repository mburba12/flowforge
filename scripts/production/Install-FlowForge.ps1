<#
.SYNOPSIS
    Creates .env.production with freshly generated secrets (only if it does not exist).
.DESCRIPTION
    Generates the database owner password, the restricted runtime role password and the
    JWT signing key. Values are never printed. The file is gitignored (.env.*).
    Re-running is safe: an existing file is left untouched unless -Force is given, and
    -Force is refused once the production database volume exists (the passwords are
    baked into it on first start).
#>
[CmdletBinding()]
param([string]$EnvFile, [switch]$Force)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
if (-not $EnvFile) { $EnvFile = Join-Path (Get-FFRoot) ".env.production" }

if ((Test-Path -LiteralPath $EnvFile) -and -not $Force) {
    Write-Host "EXISTS: $EnvFile (left unchanged)"
    return
}
if ($Force -and (docker volume ls -q --filter "name=^flowforge_flowforge_pgdata$")) {
    throw "Refusing -Force: the production database volume already uses the current passwords."
}

$content = @(
    "# FlowForge production secrets. Generated $(Get-Date -Format s). Do not commit.",
    "FLOWFORGE_DB_OWNER_PASSWORD=$(New-FFSecret 24)",
    "FLOWFORGE_APP_DB_PASSWORD=$(New-FFSecret 24)",
    "FLOWFORGE_JWT_SECRET=$(New-FFSecret 48)",
    "FF_WEB_PORT=3000",
    "FF_API_PORT=8000",
    "FF_DB_PORT=5435"
) -join "`n"
[IO.File]::WriteAllText($EnvFile, $content + "`n", (New-Object Text.UTF8Encoding($false)))
& git -C (Get-FFRoot) check-ignore -q -- $EnvFile
if ($LASTEXITCODE -ne 0) { throw "$EnvFile is not gitignored; refusing to keep secrets there." }
Write-Host "CREATED: $EnvFile (secrets generated, not displayed)"

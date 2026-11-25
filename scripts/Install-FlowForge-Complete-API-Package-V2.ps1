$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\mackb\Downloads\Download the FlowForge Phase 1 scaffold\flowforge-phase1"
$SearchRoot = "C:\Users\mackb\Downloads"

Set-Location $ProjectRoot

$PackageRoot = Get-ChildItem -LiteralPath $SearchRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "*complete API folder with database schemas and migrations*" } |
    ForEach-Object {
        Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq "FlowForge_All_Required_APIs_With_Database" }
    } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $PackageRoot) {
    $PackageRoot = Get-ChildItem -LiteralPath $SearchRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq "FlowForge_All_Required_APIs_With_Database" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

if (-not $PackageRoot) {
    throw "Extracted FlowForge_All_Required_APIs_With_Database folder was not found."
}

$Required = @(
    "FlowForge_All_Required_APIs.openapi.json",
    "FlowForge_All_Required_APIs_Manifest.csv",
    "flowforge_all_required_apis.py",
    "DATABASE_MANIFEST.json",
    "database\models.py",
    "database\schemas.py",
    "database\schema.sql",
    "migrations\ff_all_apis_001_create_flowforge_all_api_tables.py"
)
foreach ($Relative in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot.FullName $Relative))) {
        throw "Package file missing: $Relative"
    }
}

$InstallRoot = Join-Path $ProjectRoot "architecture\complete_api_contract"
$DatabaseRoot = Join-Path $InstallRoot "database"
$ProposedMigrationRoot = Join-Path $InstallRoot "proposed_migrations"
New-Item -ItemType Directory -Force -Path $InstallRoot, $DatabaseRoot, $ProposedMigrationRoot, ".\var" | Out-Null

Copy-Item -LiteralPath (Join-Path $PackageRoot.FullName "FlowForge_All_Required_APIs.openapi.json") -Destination $InstallRoot -Force
Copy-Item -LiteralPath (Join-Path $PackageRoot.FullName "FlowForge_All_Required_APIs_Manifest.csv") -Destination $InstallRoot -Force
Copy-Item -LiteralPath (Join-Path $PackageRoot.FullName "flowforge_all_required_apis.py") -Destination $InstallRoot -Force
Copy-Item -LiteralPath (Join-Path $PackageRoot.FullName "DATABASE_MANIFEST.json") -Destination $InstallRoot -Force
Copy-Item -LiteralPath (Join-Path $PackageRoot.FullName "README_FlowForge_All_Required_APIs.md") -Destination $InstallRoot -Force
Get-ChildItem -LiteralPath (Join-Path $PackageRoot.FullName "database") -Force |
    Copy-Item -Destination $DatabaseRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $PackageRoot.FullName "migrations\ff_all_apis_001_create_flowforge_all_api_tables.py") -Destination $ProposedMigrationRoot -Force

$InstalledSchema = Join-Path $DatabaseRoot "schema.sql"
if (-not (Test-Path -LiteralPath $InstalledSchema)) {
    throw "Database schema copy failed: $InstalledSchema"
}

# Audit proposed tables against the live database. Do not put an unsafe collision-heavy
# migration into migrations/versions until this gate passes.
$Manifest = Get-Content (Join-Path $InstallRoot "DATABASE_MANIFEST.json") -Raw | ConvertFrom-Json
$ProposedTables = Select-String -Path $InstalledSchema -Pattern '^CREATE TABLE IF NOT EXISTS "([^"]+)"' |
    ForEach-Object { $_.Matches[0].Groups[1].Value } |
    Sort-Object -Unique

$ExistingTables = @(
    docker compose exec -T postgres psql `
        -P pager=off `
        -v ON_ERROR_STOP=1 `
        -U flowforge `
        -d flowforge `
        -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;"
) | ForEach-Object { "$($_)".Trim() } | Where-Object { $_ }

if ($LASTEXITCODE -ne 0) {
    throw "Could not inventory the existing FlowForge database."
}

$Collisions = @($ProposedTables | Where-Object { $_ -in $ExistingTables })
$NewTables = @($ProposedTables | Where-Object { $_ -notin $ExistingTables })
$Report = [ordered]@{
    package_source = $PackageRoot.FullName
    installed_contract_path = $InstallRoot
    proposed_table_count = $ProposedTables.Count
    existing_table_count = $ExistingTables.Count
    collision_count = $Collisions.Count
    new_table_count = $NewTables.Count
    collisions = $Collisions
    new_tables = $NewTables
    migration_state = if ($Collisions.Count) { "PROPOSED_ONLY_BLOCKED_BY_COLLISIONS" } else { "ELIGIBLE_FOR_REVIEW" }
}
$Report | ConvertTo-Json -Depth 20 | Set-Content ".\var\complete_api_database_install_report.json" -Encoding UTF8

$Python = ".\.venv\Scripts\python.exe"
& $Python -m py_compile `
    (Join-Path $DatabaseRoot "models.py") `
    (Join-Path $DatabaseRoot "schemas.py") `
    (Join-Path $ProposedMigrationRoot "ff_all_apis_001_create_flowforge_all_api_tables.py")
if ($LASTEXITCODE -ne 0) { throw "Installed database package failed Python compilation." }

Write-Host "PACKAGE SOURCE:       $($PackageRoot.FullName)"
Write-Host "INSTALLED CONTRACT:   $InstallRoot"
Write-Host "PROPOSED TABLES:      $($ProposedTables.Count)"
Write-Host "EXISTING TABLES:      $($ExistingTables.Count)"
Write-Host "TABLE COLLISIONS:     $($Collisions.Count)"
Write-Host "NET-NEW TABLES:       $($NewTables.Count)"
Write-Host "AUDIT REPORT:         .\var\complete_api_database_install_report.json"

if ($Collisions.Count -gt 0) {
    Write-Host ""
    Write-Host "FLOWFORGE COMPLETE API PACKAGE INSTALLED FOR SAFE INTEGRATION" -ForegroundColor Green
    Write-Host "MIGRATION NOT APPLIED: existing FlowForge tables overlap the generated schema." -ForegroundColor Yellow
    Write-Host "The proposed migration is isolated under architecture\complete_api_contract\proposed_migrations." -ForegroundColor Yellow
} else {
    Write-Host "FLOWFORGE COMPLETE API PACKAGE INSTALLED AND READY FOR MIGRATION REVIEW" -ForegroundColor Green
}

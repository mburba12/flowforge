[CmdletBinding()]
param(
    [string]$ProjectRoot = (
        "C:\Users\mackb\Downloads\Download the FlowForge Phase 1 scaffold\flowforge-phase1"
    ),
    [string]$OutputDirectory = "$HOME\Downloads\flowforge-part2b-context",
    [string]$ApiBaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
Set-Location -LiteralPath $ProjectRoot

if (Test-Path -LiteralPath $OutputDirectory) {
    Remove-Item -LiteralPath $OutputDirectory -Recurse -Force
}

New-Item `
    -ItemType Directory `
    -Path $OutputDirectory `
    -Force |
    Out-Null

$SourceOutput = Join-Path $OutputDirectory "01-source.txt"
$OpenApiOutput = Join-Path $OutputDirectory "02-openapi.json"
$DatabaseOutput = Join-Path $OutputDirectory "03-database-schema.txt"
$RoutesOutput = Join-Path $OutputDirectory "04-frontend-routes.txt"
$GitOutput = Join-Path $OutputDirectory "05-git-state.txt"
$ManifestOutput = Join-Path $OutputDirectory "manifest.json"

Invoke-WebRequest `
    -Uri "$ApiBaseUrl/openapi.json" `
    -OutFile $OpenApiOutput `
    -UseBasicParsing

$AllowedExtensions = @(
    ".py", ".pyi",
    ".ts", ".tsx",
    ".js", ".jsx",
    ".mjs", ".cjs",
    ".json",
    ".css", ".scss",
    ".html",
    ".md", ".txt",
    ".toml", ".ini", ".cfg",
    ".yaml", ".yml",
    ".sql",
    ".ps1", ".sh"
)

$AllowedExactNames = @(
    "Dockerfile",
    ".dockerignore",
    ".gitignore",
    ".npmrc"
)

$ExcludedDirectories = @(
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".next",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    "htmlcov",
    "var",
    "backups",
    "logs",
    "tmp",
    "uploads"
)

$ExcludedNames = @(
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test"
)

$Files = @(
    Get-ChildItem `
        -LiteralPath $ProjectRoot `
        -Recurse `
        -File |
        Where-Object {
            $RelativePath = $_.FullName.Substring(
                $ProjectRoot.Length
            ).TrimStart("\")

            $PathParts = $RelativePath -split "[\\/]"

            $DirectoryAllowed = -not (
                $PathParts |
                    Where-Object {
                        $ExcludedDirectories -contains $_
                    }
            )

            $NameAllowed =
                $ExcludedNames -notcontains $_.Name

            $TypeAllowed =
                (
                    $AllowedExtensions -contains
                    $_.Extension.ToLowerInvariant()
                ) -or (
                    $AllowedExactNames -contains
                    $_.Name
                )

            $DirectoryAllowed -and
            $NameAllowed -and
            $TypeAllowed
        } |
        Sort-Object FullName
)

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$Writer = New-Object System.IO.StreamWriter(
    $SourceOutput,
    $false,
    $Utf8
)

try {
    $Writer.WriteLine(
        "FLOWFORGE PART 2B COMPLETE CONTEXT"
    )
    $Writer.WriteLine(
        "Generated: $([DateTime]::UtcNow.ToString('o'))"
    )
    $Writer.WriteLine(
        "Project root: $ProjectRoot"
    )
    $Writer.WriteLine(
        "Git commit: $((git rev-parse HEAD).Trim())"
    )
    $Writer.WriteLine(
        "Git branch: $((git branch --show-current).Trim())"
    )
    $Writer.WriteLine(
        "Included files: $($Files.Count)"
    )

    foreach ($File in $Files) {
        $RelativePath = $File.FullName.Substring(
            $ProjectRoot.Length
        ).TrimStart("\")

        $Writer.WriteLine("")
        $Writer.WriteLine("=" * 100)
        $Writer.WriteLine("FILE: $RelativePath")
        $Writer.WriteLine("=" * 100)

        try {
            $Writer.WriteLine(
                [IO.File]::ReadAllText(
                    $File.FullName
                )
            )
        }
        catch {
            $Writer.WriteLine(
                "[FILE COULD NOT BE READ: " +
                "$($_.Exception.Message)]"
            )
        }
    }
}
finally {
    $Writer.Dispose()
}

$DatabaseSql = @'
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    c.relrowsecurity AS rls_enabled,
    c.relforcerowsecurity AS rls_forced,
    a.attname AS column_name,
    pg_catalog.format_type(
        a.atttypid,
        a.atttypmod
    ) AS data_type,
    a.attnotnull AS not_null
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n
    ON n.oid = c.relnamespace
JOIN pg_catalog.pg_attribute a
    ON a.attrelid = c.oid
WHERE n.nspname = 'public'
  AND c.relkind = 'r'
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY c.relname, a.attnum;
'@

$DatabaseSql |
    docker compose exec -T postgres `
        psql `
        -U flowforge `
        -d flowforge `
        -At `
        -F "|" `
        -v ON_ERROR_STOP=1 |
    Set-Content `
        -LiteralPath $DatabaseOutput `
        -Encoding UTF8

if ($LASTEXITCODE -ne 0) {
    throw "Database schema export failed."
}

$RouteFiles = @(
    Get-ChildItem `
        -LiteralPath (Join-Path $ProjectRoot "web\src\app") `
        -Recurse `
        -File `
        -Include "page.tsx", "route.ts" |
        Sort-Object FullName
)

$RouteLines = @(
    foreach ($RouteFile in $RouteFiles) {
        $RelativePath = $RouteFile.FullName.Substring(
            $ProjectRoot.Length
        ).TrimStart("\")

        $Content = [IO.File]::ReadAllText(
            $RouteFile.FullName
        )

        $DemoMarkers = @(
            "demo-data",
            "Demo mode",
            "demonstration content",
            "Production actions remain disabled",
            "coming soon",
            "placeholder",
            "BackendFeatureWorkspace"
        ) |
            Where-Object {
                $Content.Contains($_)
            }

        [PSCustomObject]@{
            Path = $RelativePath
            DemoMarkers = (
                $DemoMarkers -join ", "
            )
            UsesFetch = (
                $Content -match "fetch\("
            )
            UsesApi = (
                $Content -match
                "api(Get|Post|Put|Patch|Delete|Request)"
            )
        }
    }
)

$RouteLines |
    ConvertTo-Json -Depth 5 |
    Set-Content `
        -LiteralPath $RoutesOutput `
        -Encoding UTF8

$GitState = @(
    "HEAD"
    git rev-parse HEAD

    ""
    "BRANCH"
    git branch --show-current

    ""
    "TAGS AT HEAD"
    git tag --points-at HEAD

    ""
    "STATUS"
    git status --short

    ""
    "RECENT COMMITS"
    git log -10 --oneline --decorate

    ""
    "ALEMBIC HEADS"
    & ".\.venv\Scripts\python.exe" `
        -m alembic heads

    ""
    "ALEMBIC CURRENT"
    & ".\.venv\Scripts\python.exe" `
        -m alembic current
)

$GitState |
    Set-Content `
        -LiteralPath $GitOutput `
        -Encoding UTF8

$Manifest = [ordered]@{
    generated_at = [DateTime]::UtcNow.ToString("o")
    project_root = $ProjectRoot
    git_commit = (git rev-parse HEAD).Trim()
    branch = (git branch --show-current).Trim()
    source_files = $Files.Count
    outputs = @(
        "01-source.txt",
        "02-openapi.json",
        "03-database-schema.txt",
        "04-frontend-routes.txt",
        "05-git-state.txt"
    )
    excluded = @(
        "environment files",
        "real secrets",
        "Git internals",
        "virtual environments",
        "node_modules",
        "build output",
        "backups",
        "uploads",
        "logs"
    )
}

$Manifest |
    ConvertTo-Json -Depth 10 |
    Set-Content `
        -LiteralPath $ManifestOutput `
        -Encoding UTF8

Get-ChildItem `
    -LiteralPath $OutputDirectory `
    -File |
    ForEach-Object {
        $Hash = Get-FileHash `
            -LiteralPath $_.FullName `
            -Algorithm SHA256

        Write-Host (
            "{0} | {1} bytes | {2}" -f
            $_.Name,
            $_.Length,
            $Hash.Hash
        ) -ForegroundColor Green
    }

Write-Host ""
Write-Host (
    "PART 2B CONTEXT READY: $OutputDirectory"
) -ForegroundColor Green
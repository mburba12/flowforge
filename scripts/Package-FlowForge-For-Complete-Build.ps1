$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\mackb\Downloads\Download the FlowForge Phase 1 scaffold\flowforge-phase1"
$Output = "C:\Users\mackb\Downloads\flowforge-complete-build-source.zip"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "FlowForge project not found: $ProjectRoot"
}

$Required = @(
    "src",
    "tests",
    "web",
    "migrations",
    "scripts",
    "infra",
    "config",
    "architecture",
    "pyproject.toml",
    "alembic.ini"
)
foreach ($Item in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot $Item))) {
        throw "Required project item missing: $Item"
    }
}

$ForbiddenPatterns = @(
    '(?i)(^|[\\/])\.env($|\.)',
    '(?i)\.pem$',
    '(?i)\.pfx$',
    '(?i)\.key$',
    '(?i)\.dump$',
    '(?i)(^|[\\/])node_modules([\\/]|$)',
    '(?i)(^|[\\/])\.venv([\\/]|$)',
    '(?i)(^|[\\/])\.git([\\/]|$)',
    '(?i)(^|[\\/])\.next([\\/]|$)',
    '(?i)(^|[\\/])__pycache__([\\/]|$)',
    '(?i)(^|[\\/])playwright-report([\\/]|$)',
    '(?i)(^|[\\/])test-results([\\/]|$)',
    '(?i)(^|[\\/])var[\\/]backups([\\/]|$)'
)

$Files = Get-ChildItem -LiteralPath $ProjectRoot -File -Recurse -Force | Where-Object {
    $Relative = $_.FullName.Substring($ProjectRoot.Length).TrimStart('\')
    -not ($ForbiddenPatterns | Where-Object { $Relative -match $_ })
}

if (-not $Files) {
    throw "No project files selected."
}

$HighConfidencePatterns = @(
    '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'AccountKey=[A-Za-z0-9+/]{40,}={0,2}',
    'ghp_[A-Za-z0-9]{30,}',
    'github_pat_[A-Za-z0-9_]{40,}',
    'sk_live_[A-Za-z0-9]{20,}',
    'AKIA[0-9A-Z]{16}'
)
$TextExtensions = @('.py','.ps1','.ts','.tsx','.js','.json','.toml','.ini','.yml','.yaml','.bicep','.md','.sql')
$SecretHits = foreach ($File in $Files | Where-Object { $_.Extension -in $TextExtensions }) {
    Select-String -LiteralPath $File.FullName -Pattern $HighConfidencePatterns -ErrorAction SilentlyContinue
}
if ($SecretHits) {
    $SecretHits | Select-Object Path, LineNumber | Format-Table -AutoSize
    throw "High-confidence secret material detected. Remove or rotate it before packaging."
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $Output) { Remove-Item -LiteralPath $Output -Force }
$Archive = [System.IO.Compression.ZipFile]::Open($Output, 'Create')
try {
    foreach ($File in $Files) {
        $Relative = $File.FullName.Substring($ProjectRoot.Length).TrimStart('\')
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $Archive,
            $File.FullName,
            $Relative,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
}
finally {
    $Archive.Dispose()
}

$Size = (Get-Item -LiteralPath $Output).Length
if ($Size -lt 1024) { throw "Created ZIP is unexpectedly small." }
Write-Host "CREATED: $Output" -ForegroundColor Green
Write-Host "FILES:   $($Files.Count)"
Write-Host "BYTES:   $Size"

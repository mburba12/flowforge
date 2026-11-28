# Shared helpers for the FlowForge production scripts. Dot-source; do not run.
Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

$script:Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$script:ComposeFile = Join-Path $script:Root "compose.production.yml"
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Get-FFRoot { $script:Root }

function Read-FFEnvFile([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "Environment file not found: $Path" }
    $values = @{}
    foreach ($line in [IO.File]::ReadAllLines($Path)) {
        if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
        $key, $value = $line -split '=', 2
        $values[$key.Trim()] = $value.Trim()
    }
    return $values
}

function Invoke-FFNative {
    # Runs a native command with stderr merged (PowerShell 5.1 safe) and fails on non-zero exit.
    param([Parameter(Mandatory)][string]$Description, [Parameter(Mandatory)][scriptblock]$Command)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { $output = & $Command 2>&1 | ForEach-Object { "$_" }; $code = $LASTEXITCODE }
    finally { $ErrorActionPreference = $previous }
    if ($code -ne 0) {
        $tail = ($output | Select-Object -Last 15) -join [Environment]::NewLine
        throw "$Description failed (exit $code).$([Environment]::NewLine)$tail"
    }
    return $output
}

function Invoke-FFCompose {
    param(
        [string]$Project = "flowforge",
        [string]$EnvFile = (Join-Path $script:Root ".env.production"),
        [Parameter(Mandatory)][string[]]$Arguments,
        [string]$Description = "docker compose"
    )
    if (-not (Test-Path -LiteralPath $EnvFile)) { throw "Missing $EnvFile. Run scripts\production\Install-FlowForge.ps1 first." }
    $all = @("compose", "-p", $Project, "-f", $script:ComposeFile, "--env-file", $EnvFile) + $Arguments
    Invoke-FFNative -Description "$Description" -Command { docker @all }
}

function Get-FFContainer([string]$Project, [string]$Service) {
    $id = (docker ps -q --filter "label=com.docker.compose.project=$Project" --filter "label=com.docker.compose.service=$Service" | Select-Object -First 1)
    if (-not $id) { throw "No running container for $Project/$Service" }
    return $id.Trim()
}

function Wait-FFHttp([string]$Url, [int]$TimeoutSeconds = 180) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try { if ((Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200) { return } } catch { }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for $Url"
}

function Write-FFLog([string]$Message, [string]$LogFile) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ss"), $Message
    Write-Host $line
    if ($LogFile) { Add-Content -Path $LogFile -Value $line -Encoding UTF8 }
}

function New-FFKey {
    # 32 random bytes, base64: an AES-256 key (FLOWFORGE_CREDENTIALS_KEY, FLOWFORGE_BACKUP_KEY).
    $buffer = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($buffer)
    return [Convert]::ToBase64String($buffer)
}

function New-FFSecret([int]$Bytes = 32) {
    $buffer = New-Object byte[] $Bytes
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($buffer)
    return (($buffer | ForEach-Object { $_.ToString("x2") }) -join "")
}

function ConvertTo-FFLibpqDsn([string]$SqlAlchemyUrl, [string]$HostName, [int]$Port) {
    # postgresql+asyncpg://user:pass@host:port/db -> postgresql://user:pass@HostName:Port/db (escaped)
    if ($SqlAlchemyUrl -notmatch '^[a-z+]+://([^:]+):([^@]*)@[^/]+/(.+)$') { throw "Unrecognised database URL format" }
    $user = [uri]::EscapeDataString([uri]::UnescapeDataString($Matches[1]))
    $pass = [uri]::EscapeDataString([uri]::UnescapeDataString($Matches[2]))
    return "postgresql://${user}:${pass}@${HostName}:${Port}/$($Matches[3])"
}

function Invoke-FFCrypt {
    # Runs scripts\production\ffcrypt.py with the backup key in its environment only.
    param([Parameter(Mandatory)][string]$Key, [Parameter(Mandatory)][string[]]$Arguments)
    $python = Join-Path (Get-FFRoot) ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) { throw "Python environment not found: $python" }
    $tool = Join-Path $PSScriptRoot "ffcrypt.py"
    $previous = $env:FLOWFORGE_BACKUP_KEY
    $env:FLOWFORGE_BACKUP_KEY = $Key
    try {
        $output = & $python -I $tool @Arguments 2>&1 | ForEach-Object { "$_" }
        if ($LASTEXITCODE -ne 0) { throw "ffcrypt $($Arguments[0]) failed: $($output -join ' ')" }
        return $output
    } finally {
        $env:FLOWFORGE_BACKUP_KEY = $previous
    }
}

function Protect-FFFile([string]$Path, [string]$Key) {
    # Encrypt, verify by decrypting, delete the plain file; returns the .enc path.
    return (Invoke-FFCrypt -Key $Key -Arguments @("encrypt-file", $Path) | Select-Object -Last 1).Trim()
}

function Get-FFPlainBackup([string]$Path, [string]$EnvFile = (Join-Path $script:Root ".env.production")) {
    # A plain copy of a backup for pg_restore (decrypted into var\tmp when encrypted).
    # The caller deletes the returned file when it differs from $Path.
    if (-not $Path.EndsWith(".enc")) { return $Path }
    $key = (Read-FFEnvFile $EnvFile)["FLOWFORGE_BACKUP_KEY"]
    if (-not $key) { throw "FLOWFORGE_BACKUP_KEY is needed to read $Path" }
    $tmp = Join-Path $script:Root "var\tmp"
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $plain = Join-Path $tmp ([IO.Path]::GetFileNameWithoutExtension($Path))
    Invoke-FFCrypt -Key $key -Arguments @("decrypt", $Path, $plain) | Out-Null
    return $plain
}

function Protect-FFSecretPath([string]$Path) {
    # Only this Windows account (and SYSTEM) may read the secrets file / backups folder.
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $who = "$env:USERDOMAIN\$env:USERNAME"
    $isDir = (Get-Item -LiteralPath $Path).PSIsContainer
    $grant = if ($isDir) { "(OI)(CI)F" } else { "F" }
    $out = & icacls $Path /inheritance:r /grant:r "${who}:$grant" "*S-1-5-18:$grant" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Could not restrict access to ${Path}: $out" }
}

function Set-FFEnvValues {
    # Update KEY=value lines in the secrets file in one step; no plain-text copies are left.
    param([Parameter(Mandatory)][string]$EnvFile, [Parameter(Mandatory)][hashtable]$Values)
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($l in [IO.File]::ReadAllLines($EnvFile)) { $lines.Add($l) }
    foreach ($key in $Values.Keys) {
        $value = [string]$Values[$key]
        if ($value -match '[\r\n]') { throw "$key contains a line break." }
        $index = -1
        for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match "^\s*$([regex]::Escape($key))=") { $index = $i } }
        if ($index -ge 0) { $lines[$index] = "$key=$value" } else { $lines.Add("$key=$value") }
    }
    $tmp = "$EnvFile.writing"
    [IO.File]::WriteAllLines($tmp, $lines, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $EnvFile -Force
    Protect-FFSecretPath $EnvFile
}

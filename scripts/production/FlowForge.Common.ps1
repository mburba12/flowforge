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

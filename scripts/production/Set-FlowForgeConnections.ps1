<#
.SYNOPSIS  Turn on live bank feeds (Plaid) and direct Gusto sign-in for FlowForge.
.DESCRIPTION
    Asks for the keys with hidden input, writes them to .env.production (never printed),
    and restarts the API so it picks them up. Run it once per provider; press Enter to
    skip a provider you are not setting up yet.

    Before you run it:
      Plaid  - create an account at https://dashboard.plaid.com, then Developers -> Keys.
               Start with "sandbox" (test banks, user_good / pass_good). Live banks need
               Plaid's production approval, then run this again with "production".
      Gusto  - create an app at https://dev.gusto.com. Add the redirect URL this script
               prints. Start with "demo"; Gusto approves production apps separately.
.EXAMPLE   .\scripts\production\Set-FlowForgeConnections.ps1
.EXAMPLE   .\scripts\production\Set-FlowForgeConnections.ps1 -Only Plaid
#>
[CmdletBinding()]
param(
    [ValidateSet("Both", "Plaid", "Gusto")][string]$Only = "Both",
    [string]$Project = "flowforge",
    [string]$EnvFile,
    [switch]$NoRestart
)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
if (-not $EnvFile) { $EnvFile = Join-Path (Get-FFRoot) ".env.production" }
if (-not (Test-Path $EnvFile)) { throw "Not found: $EnvFile (run Install-FlowForge.ps1 first)." }

function Read-Hidden([string]$Prompt) {
    $secure = Read-Host $Prompt -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr).Trim() }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Read-Choice([string]$Prompt, [string[]]$Allowed, [string]$Default) {
    while ($true) {
        $value = (Read-Host "$Prompt [$($Allowed -join '/')] (Enter = $Default)").Trim().ToLowerInvariant()
        if (-not $value) { return $Default }
        if ($Allowed -contains $value) { return $value }
        Write-Host "Choose one of: $($Allowed -join ', ')" -ForegroundColor Yellow
    }
}

function Set-EnvValues([hashtable]$Values) {
    $lines = [System.Collections.Generic.List[string]]::new()
    if (Test-Path $EnvFile) { foreach ($l in Get-Content -LiteralPath $EnvFile) { $lines.Add($l) } }
    foreach ($key in $Values.Keys) {
        if ($Values[$key] -match '[\r\n]') { throw "$key contains a line break." }
        $entry = "$key=$($Values[$key])"
        $index = -1
        for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match "^\s*$([regex]::Escape($key))=") { $index = $i } }
        if ($index -ge 0) { $lines[$index] = $entry } else { $lines.Add($entry) }
    }
    $backup = "$EnvFile.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Copy-Item -LiteralPath $EnvFile -Destination $backup
    [IO.File]::WriteAllLines($EnvFile, $lines, [Text.UTF8Encoding]::new($false))
    Write-Host "Saved to $EnvFile (previous copy: $backup)."
}

$cfg = Read-FFEnvFile $EnvFile
$publicUrl = $cfg["FLOWFORGE_PUBLIC_URL"]
if (-not $publicUrl) { $publicUrl = "http://localhost:3000" }
$changes = @{}

if ($Only -in @("Both", "Plaid")) {
    Write-Host "`n== Plaid (live bank feeds) ==" -ForegroundColor Cyan
    $id = Read-Hidden "Plaid client_id (Enter to skip)"
    if ($id) {
        $secret = Read-Hidden "Plaid secret for the environment you choose next"
        if (-not $secret) { throw "A Plaid secret is required." }
        $changes["FLOWFORGE_PLAID_CLIENT_ID"] = $id
        $changes["FLOWFORGE_PLAID_SECRET"] = $secret
        $changes["FLOWFORGE_PLAID_ENV"] = Read-Choice "Plaid environment" @("sandbox", "production") "sandbox"
        $id = $null; $secret = $null
    }
}

if ($Only -in @("Both", "Gusto")) {
    Write-Host "`n== Gusto (move payroll directly) ==" -ForegroundColor Cyan
    Write-Host "Register this redirect URL in your Gusto app first: $publicUrl/connections/payroll/callback"
    $id = Read-Hidden "Gusto client ID (Enter to skip)"
    if ($id) {
        $secret = Read-Hidden "Gusto client secret"
        if (-not $secret) { throw "A Gusto client secret is required." }
        $changes["FLOWFORGE_GUSTO_CLIENT_ID"] = $id
        $changes["FLOWFORGE_GUSTO_CLIENT_SECRET"] = $secret
        $changes["FLOWFORGE_GUSTO_ENV"] = Read-Choice "Gusto environment" @("demo", "production") "demo"
        $id = $null; $secret = $null
    }
}

if ($changes.Count -eq 0) { Write-Host "Nothing entered; nothing changed."; return }
if (-not $cfg["FLOWFORGE_PUBLIC_URL"]) { $changes["FLOWFORGE_PUBLIC_URL"] = $publicUrl }
Set-EnvValues $changes
$names = ($changes.Keys | Where-Object { $_ -notmatch "SECRET|CLIENT_ID" } | ForEach-Object { "$_=$($changes[$_])" }) -join ", "
$changes = $null

if ($NoRestart) { Write-Host "Restart the API to apply: .\scripts\production\Start-FlowForge.ps1"; return }
Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments @("up", "-d", "--wait", "api", "web") -Description "Restart API with new connection keys" | Out-Null
$api = Get-FFContainer $Project "api"
$check = docker exec $api python -c "from flowforge.core.config import settings as s; print('plaid=' + ('on' if s.plaid_client_id and s.plaid_secret else 'off'), 'gusto=' + ('on' if s.gusto_client_id and s.gusto_client_secret else 'off'))"
Write-Host "CONNECTIONS UPDATED ($names). Now: $check" -ForegroundColor Green
Write-Host "Open FlowForge -> Bank accounts -> Connect a bank, or Payroll -> Move from another provider -> Gusto."

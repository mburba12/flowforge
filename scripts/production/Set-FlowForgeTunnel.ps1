<#
.SYNOPSIS  Put Krov WorkAgent on the internet through Cloudflare Tunnel (or take it off).
.DESCRIPTION
    Asks for the tunnel token (hidden) and the public address, writes them to
    .env.production (a backup copy is kept), starts the "tunnel" service and checks that
    the address answers. Nothing is opened on your router: the tunnel connects out.

    Before you run it, in the Cloudflare dashboard (your domain must be on Cloudflare):
      Zero Trust -> Networks -> Tunnels -> Create a tunnel -> Cloudflared -> name it
      -> copy the token from the install command (the long string after "--token").
      Public hostname: e.g. app.yourdomain.com, Service type HTTP, URL web:3000
    Recommended: Zero Trust -> Access -> Applications -> add app.yourdomain.com with a
    policy that only lets your team's emails in (one-time email code before sign-in).
.EXAMPLE   .\scripts\production\Set-FlowForgeTunnel.ps1
.EXAMPLE   .\scripts\production\Set-FlowForgeTunnel.ps1 -Disable
#>
[CmdletBinding()]
param(
    [switch]$Disable,
    [string]$Project = "flowforge",
    [string]$EnvFile
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

function Set-EnvValues([hashtable]$Values) {
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($l in Get-Content -LiteralPath $EnvFile) { $lines.Add($l) }
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

if ($Disable) {
    Set-EnvValues @{ COMPOSE_PROFILES = ""; FLOWFORGE_TUNNEL_TOKEN = "" }
    Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments @("--profile", "tunnel", "stop", "tunnel") -Description "Stop tunnel" | Out-Null
    Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments @("--profile", "tunnel", "rm", "-f", "tunnel") -Description "Remove tunnel container" | Out-Null
    Write-Host "TUNNEL OFF. Krov WorkAgent is reachable only on this computer (http://localhost:3000)." -ForegroundColor Green
    return
}

$token = Read-Hidden "Cloudflare tunnel token"
if ($token -notmatch '^[A-Za-z0-9+/=_-]{40,}$') { throw "That does not look like a tunnel token (copy only the long string after --token)." }
$hostName = (Read-Host "Public address, for example app.yourdomain.com").Trim().ToLowerInvariant() -replace '^https?://', '' -replace '/.*$', ''
if ($hostName -notmatch '^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$') { throw "Not a host name: $hostName" }
$publicUrl = "https://$hostName"

Set-EnvValues @{ FLOWFORGE_TUNNEL_TOKEN = $token; COMPOSE_PROFILES = "tunnel"; FLOWFORGE_PUBLIC_URL = $publicUrl }
$token = $null

# api picks up the new public address (Gusto return link); tunnel starts.
Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments @("up", "-d", "--wait", "api", "web") -Description "Restart api and web" | Out-Null
Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments @("up", "-d", "tunnel") -Description "Start tunnel" | Out-Null

$tunnel = Get-FFContainer $Project "tunnel"
$connected = $false
for ($i = 0; $i -lt 30 -and -not $connected; $i++) {
    Start-Sleep -Seconds 2
    $log = (docker logs $tunnel 2>&1 | Out-String)
    if ($log -match "Registered tunnel connection") { $connected = $true }
    elseif ($log -match "Unauthorized|invalid token|token is invalid") { throw "Cloudflare refused the token. Copy it again from the tunnel page and re-run." }
}
if (-not $connected) { throw "The tunnel did not connect within a minute. See: docker logs $tunnel" }
Write-Host "Tunnel connected to Cloudflare." -ForegroundColor Green

$ok = $false
for ($i = 0; $i -lt 10 -and -not $ok; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$publicUrl/login" -UseBasicParsing -TimeoutSec 15 -MaximumRedirection 5
        $ok = $r.StatusCode -eq 200
    } catch { Start-Sleep -Seconds 3 }
}
if ($ok) {
    Write-Host "KROV WORKAGENT IS LIVE at $publicUrl" -ForegroundColor Green
} else {
    Write-Warning "The tunnel is up but $publicUrl/login did not answer 200 yet. In Cloudflare, check the public hostname's service is HTTP and web:3000 (or Access is asking for a login first, which is fine)."
}
Write-Host "If you use Gusto, change its redirect URL to $publicUrl/connections/payroll/callback"

<#
.SYNOPSIS  Turn on Plaid (bank feeds), Gusto (payroll switch), Stripe (card billing) and invoice email.
.DESCRIPTION
    Asks for the keys with hidden input, writes them to .env.production (never printed, no copies kept),
    and restarts the API so it picks them up. Run it once per provider; press Enter to
    skip a provider you are not setting up yet.

    Before you run it:
      Plaid  - create an account at https://dashboard.plaid.com, then Developers -> Keys.
               Start with "sandbox" (test banks, user_good / pass_good). Live banks need
               Plaid's production approval, then run this again with "production".
      Gusto  - create an app at https://dev.gusto.com. Add the redirect URL this script
               prints. Start with "demo"; Gusto approves production apps separately.
      Stripe - https://dashboard.stripe.com -> Developers -> API keys -> Secret key
               (sk_test_... to try with test cards, sk_live_... to charge real cards).
      Email  - any SMTP service for invoice emails (Postmark, Amazon SES, Microsoft 365,
               Google Workspace). You need its server name, port, user name, password and
               a From address on your own domain, e.g. billing@krovworkagent.com.
.EXAMPLE   .\scripts\production\Set-FlowForgeConnections.ps1
.EXAMPLE   .\scripts\production\Set-FlowForgeConnections.ps1 -Only Plaid
#>
[CmdletBinding()]
param(
    [ValidateSet("All", "Both", "Plaid", "Gusto", "Stripe", "Email")][string]$Only = "All",
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
    Set-FFEnvValues -EnvFile $EnvFile -Values $Values
    Write-Host "Saved to $EnvFile."
}

$cfg = Read-FFEnvFile $EnvFile
$publicUrl = $cfg["FLOWFORGE_PUBLIC_URL"]
if (-not $publicUrl) { $publicUrl = "http://localhost:3000" }
$changes = @{}

if ($Only -in @("All", "Both", "Plaid")) {
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

if ($Only -in @("All", "Both", "Gusto")) {
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

if ($Only -in @("All", "Stripe")) {
    Write-Host "`n== Stripe (charge customers' cards for their monthly invoices) ==" -ForegroundColor Cyan
    $key = Read-Hidden "Stripe secret key, sk_test_... or sk_live_... (Enter to skip)"
    if ($key) {
        if ($key -notmatch '^(sk|rk)_(test|live)_[A-Za-z0-9]+$') { throw "That does not look like a Stripe secret key." }
        $changes["FLOWFORGE_STRIPE_SECRET_KEY"] = $key
        if ($key -match '_test_') { Write-Host "Test mode: use card 4242 4242 4242 4242, any future date and CVC." }
        $key = $null
    }
}

if ($Only -in @("All", "Email")) {
    Write-Host "`n== Invoice email (SMTP) ==" -ForegroundColor Cyan
    $smtpHost = (Read-Host "SMTP server, e.g. smtp.postmarkapp.com (Enter to skip)").Trim()
    if ($smtpHost) {
        $port = (Read-Host "Port (Enter = 587)").Trim()
        if (-not $port) { $port = "587" }
        if ($port -notmatch '^\d+$') { throw "The port must be a number." }
        $user = Read-Hidden "SMTP user name"
        $pass = Read-Hidden "SMTP password"
        $from = (Read-Host "From address, e.g. Krov WorkAgent <billing@yourdomain.com>").Trim()
        if (-not $from) { throw "A From address is required." }
        $changes["FLOWFORGE_SMTP_HOST"] = $smtpHost
        $changes["FLOWFORGE_SMTP_PORT"] = $port
        $changes["FLOWFORGE_SMTP_USERNAME"] = $user
        $changes["FLOWFORGE_SMTP_PASSWORD"] = $pass
        $changes["FLOWFORGE_MAIL_FROM"] = $from
        $user = $null; $pass = $null
    }
}

if ($changes.Count -eq 0) { Write-Host "Nothing entered; nothing changed."; return }
if (-not $cfg["FLOWFORGE_PUBLIC_URL"]) { $changes["FLOWFORGE_PUBLIC_URL"] = $publicUrl }
Set-EnvValues $changes
$names = ($changes.Keys | Where-Object { $_ -notmatch "SECRET|CLIENT_ID|PASSWORD|USERNAME" } | ForEach-Object { "$_=$($changes[$_])" }) -join ", "
$changes = $null

if ($NoRestart) { Write-Host "Restart the API to apply: .\scripts\production\Start-FlowForge.ps1"; return }
Invoke-FFCompose -Project $Project -EnvFile $EnvFile -Arguments @("up", "-d", "--wait", "api", "web") -Description "Restart API with new connection keys" | Out-Null
$api = Get-FFContainer $Project "api"
$check = docker exec $api python -c "from flowforge.core.config import settings as s; print('plaid=' + ('on' if s.plaid_client_id and s.plaid_secret else 'off'), 'gusto=' + ('on' if s.gusto_client_id and s.gusto_client_secret else 'off'), 'stripe=' + ('test' if s.stripe_secret_key.startswith(('sk_test','rk_test')) else 'live' if s.stripe_secret_key else 'off'), 'email=' + ('on' if s.smtp_host and s.mail_from else 'off'))"
Write-Host "CONNECTIONS UPDATED ($names). Now: $check" -ForegroundColor Green
Write-Host "Open FlowForge -> Bank accounts -> Connect a bank, or Payroll -> Move from another provider -> Gusto."

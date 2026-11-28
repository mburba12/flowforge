<#
.SYNOPSIS  Switch on the remaining security settings. Your new admin password is the last thing it asks.
.DESCRIPTION
    Run once, after the security release is live. It first checks everything and asks its
    questions; your new password comes last. Then it applies, in this order:

      1. A dedicated encryption key for stored secrets (bank, Gusto and carrier credentials,
         worker bank and routing numbers, tax registration numbers, uploaded files,
         authenticator secrets) and a separate key for backups.
      2. Moves every stored secret and file onto the new key (each value checked).
      3. A new sign-in signing key: everyone, including old stolen sessions, is signed out.
      4. Encrypts every existing backup and the old release export; deletes the plain copies
         only after each encrypted copy has been checked. Deletes the old plain copy of the
         settings file.
      5. Locks the settings files and backup folders to your Windows account.
      6. A daily encrypted backup at 2:30 AM, copied to your off-computer folder.
      7. Your new admin password (every old sign-in ends); removes the old temporary
         password from the release record.
      8. Checks the whole system.

    At your next sign-in Krov WorkAgent asks you to set up two-step sign-in (an authenticator
    app on your phone). Safe to run again; it never prints a secret unless you ask it to.
.EXAMPLE   .\scripts\production\Complete-FlowForgeSecurity.ps1
#>
[CmdletBinding()]
param([string]$Project = "flowforge", [string]$TenantSlug = "flowforge-production")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")
$root = Get-FFRoot
$envFile = Join-Path $root ".env.production"
$cfg = Read-FFEnvFile $envFile
$db = Get-FFContainer $Project "db"
function Sql([string]$Query) { ($Query | docker exec -i $db psql -U flowforge_owner -d flowforge -v ON_ERROR_STOP=1 -At) }
function Say([string]$Text, [string]$Color = "White") { Write-Host $Text -ForegroundColor $Color }
function Read-Secure([string]$Prompt) { Read-Host $Prompt -AsSecureString }
function Plain([SecureString]$S) {
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($S)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}

# ------------------------------------------------------------------ checks (no changes)
Say "`n== Checking ==" Cyan
$head = (Sql "SELECT version_num FROM alembic_version").Trim()
if ($head -ne "ff_security_002") { throw "The security release is not live yet (database at $head). Run .\scripts\production\Update-FlowForge.ps1 first." }
if (-not (Test-Path (Join-Path $root ".venv\Scripts\python.exe"))) { throw "Python environment (.venv) not found." }
$ownerEmail = (Sql "SELECT u.email FROM users u JOIN user_roles ur ON ur.user_id = u.id JOIN roles r ON r.id = ur.role_id JOIN tenants t ON t.id = u.tenant_id WHERE t.slug = '$TenantSlug' AND r.name = 'Owner' AND u.is_active ORDER BY u.created_at LIMIT 1").Trim()
if (-not $ownerEmail) { throw "No active owner found in $TenantSlug." }
Say "Admin account: $ownerEmail"
$diskNote = "unknown"
try {
    $vol = Get-BitLockerVolume -MountPoint $env:SystemDrive -ErrorAction Stop
    $diskNote = "$($vol.VolumeStatus), protection $($vol.ProtectionStatus)"
} catch {
    $diskNote = "could not be read without administrator rights"
}
Say "Disk encryption (BitLocker / device encryption) on ${env:SystemDrive}: $diskNote"

# ------------------------------------------------------------------ questions
Say "`n== A few questions (your new password is last) ==" Cyan
$defaultOffsite = if ($env:OneDrive) { Join-Path $env:OneDrive "Krov WorkAgent Backups" } else { "" }
$current = $cfg["FLOWFORGE_BACKUP_OFFSITE_DIR"]
$suggest = if ($current) { $current } else { $defaultOffsite }
$answer = (Read-Host "Folder for off-computer backup copies (a OneDrive or external-drive folder). Enter = $(if ($suggest) { $suggest } else { 'none' }), or type 'none'").Trim()
$offsite = if ($answer -eq "none") { "" } elseif ($answer) { $answer } else { $suggest }

$turnstileSite = $cfg["FLOWFORGE_TURNSTILE_SITE_KEY"]
$turnstileSecret = $null
$t = (Read-Host "Cloudflare Turnstile site key for the robot check on sign-up (Enter to $(if ($turnstileSite) { 'keep the current one' } else { 'skip' }))").Trim()
if ($t) {
    $turnstileSite = $t
    $turnstileSecret = Plain (Read-Secure "Cloudflare Turnstile secret key")
    if (-not $turnstileSecret) { throw "The Turnstile secret key is required with a site key." }
}

$showKey = (Read-Host "Show the backup key once at the end so you can save it in your password manager? [Y/n]").Trim().ToLower() -ne "n"

Say "`nLast step: your new admin password (at least 12 characters; it is never shown)." Yellow
$pw1 = Read-Secure "New password for $ownerEmail"
$pw2 = Read-Secure "Repeat the new password"
if ((Plain $pw1) -ne (Plain $pw2)) { throw "The passwords do not match. Nothing was changed." }
if ((Plain $pw1).Length -lt 12) { throw "Use at least 12 characters. Nothing was changed." }
$pw2 = $null

# ------------------------------------------------------------------ apply
Say "`n== Applying the security settings ==" Cyan
$step = 0
function Done([string]$Text) { $script:step++; Say ("{0}. {1}" -f $script:step, $Text) Green }

# 1. Keys
$values = @{}
if (-not $cfg["FLOWFORGE_CREDENTIALS_KEY"]) { $values["FLOWFORGE_CREDENTIALS_KEY"] = New-FFKey }
if (-not $cfg["FLOWFORGE_BACKUP_KEY"]) { $values["FLOWFORGE_BACKUP_KEY"] = New-FFKey }
$values["FLOWFORGE_BACKUP_OFFSITE_DIR"] = $offsite
if ($turnstileSecret) { $values["FLOWFORGE_TURNSTILE_SITE_KEY"] = $turnstileSite; $values["FLOWFORGE_TURNSTILE_SECRET"] = $turnstileSecret }
Set-FFEnvValues -EnvFile $envFile -Values $values
$values = $null; $turnstileSecret = $null
$cfg = Read-FFEnvFile $envFile
Invoke-FFCompose -Project $Project -Arguments @("up", "-d", "--wait", "api", "web") -Description "Restart with the new key" | Out-Null
Done "Dedicated encryption keys in place (stored secrets and backups use separate keys)."

# 2. Re-encrypt everything stored
$report = Invoke-FFCompose -Project $Project -Arguments @("run", "--rm", "migrate", "python", "-m", "flowforge.accounts.reencrypt") -Description "Re-encrypt" 2>&1
$report | Where-Object { $_ -match "to update|UNREADABLE|  \S" } | ForEach-Object { Say "   $_" }
Invoke-FFCompose -Project $Project -Arguments @("run", "--rm", "migrate", "python", "-m", "flowforge.accounts.reencrypt", "--check") -Description "Re-encryption check" | Out-Null
Done "Every stored secret and uploaded file is encrypted with the new key (checked)."

# 3. New sign-in signing key (signs everyone out)
Set-FFEnvValues -EnvFile $envFile -Values @{ FLOWFORGE_JWT_SECRET = (New-FFSecret 48) }
$cfg = Read-FFEnvFile $envFile
Invoke-FFCompose -Project $Project -Arguments @("up", "-d", "--wait", "api", "web") -Description "Restart with the new signing key" | Out-Null
Invoke-FFCompose -Project $Project -Arguments @("run", "--rm", "migrate", "python", "-m", "flowforge.accounts.reencrypt", "--check") -Description "Check after key change" | Out-Null
Done "New sign-in signing key; every existing session has ended."

# 4. Encrypt old backups and exports; remove plain copies of secrets
$backupKey = $cfg["FLOWFORGE_BACKUP_KEY"]
foreach ($folder in @((Join-Path $root "var\backups"), (Join-Path $root "var\cutover"), (Join-Path $root "release-20261127-154058"))) {
    if (Test-Path $folder) {
        $manifest = Join-Path $folder "release-manifest.txt"
        $out = Invoke-FFCrypt -Key $backupKey -Arguments @("encrypt-tree", $folder)
        Say "   $($out | Select-Object -Last 1)"
    }
}
$copies = Get-ChildItem -LiteralPath $root -Filter ".env.production.bak-*" -File -Force -ErrorAction SilentlyContinue
$copies | Remove-Item -Force -Confirm:$false
Done "Existing backups and the old release export are encrypted (plain copies removed after checking); $(@($copies).Count) old settings-file copies deleted."

# 5. Lock files and folders to this Windows account
foreach ($path in @(".env.production", ".env.phase-c", ".env", ".env.local", ".env.recovered-database", "var\backups", "var\cutover", "release-20261127-154058")) {
    $full = Join-Path $root $path
    if (Test-Path -LiteralPath $full) { Protect-FFSecretPath $full }
}
if ($offsite) { New-Item -ItemType Directory -Force -Path $offsite | Out-Null }
Done "Settings files and backup folders can only be opened by your Windows account."

# 6. Daily encrypted backup
$taskName = "Krov WorkAgent daily backup"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"{0}`" -Label daily" -f (Join-Path $PSScriptRoot "Backup-FlowForge.ps1")) -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At "2:30AM"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Encrypted Krov WorkAgent database backup, copied off this computer" -Force | Out-Null
$first = & (Join-Path $PSScriptRoot "Backup-FlowForge.ps1") -Project $Project -Label "daily" | Select-Object -Last 1
Done "Daily encrypted backup at 2:30 AM$(if ($offsite) { ", copied to $offsite" }). First one made: $(Split-Path $first -Leaf)"

# 7. New admin password; remove the old temporary password from the release record
& (Join-Path $PSScriptRoot "Set-FlowForgeAdminPassword.ps1") -Email $ownerEmail -TenantSlug $TenantSlug -Project $Project -Password $pw1 | Out-Null
$pw1 = $null
$manifest = Join-Path $root "release-20261127-154058\release-manifest.txt"
$manifestEnc = "$manifest.enc"
if (Test-Path $manifestEnc) {
    $plainManifest = Join-Path $root "var\tmp\release-manifest.txt"
    New-Item -ItemType Directory -Force -Path (Split-Path $plainManifest) | Out-Null
    Invoke-FFCrypt -Key $backupKey -Arguments @("decrypt", $manifestEnc, $plainManifest) | Out-Null
    $kept = Get-Content -LiteralPath $plainManifest | Where-Object { $_ -notmatch "(?i)password|passwd|secret" }
    Set-Content -LiteralPath $plainManifest -Value $kept -Encoding utf8
    Remove-Item -LiteralPath $manifestEnc -Force -Confirm:$false
    Copy-Item -LiteralPath $plainManifest -Destination $manifest
    Remove-Item -LiteralPath $plainManifest -Force -Confirm:$false
    Invoke-FFCrypt -Key $backupKey -Arguments @("encrypt-file", $manifest) | Out-Null
}
Done "New admin password set for $ownerEmail; the temporary password was removed from the release record."

# 8. Verify
& (Join-Path $PSScriptRoot "Test-FlowForgeStack.ps1") -Project $Project -ApiPort ([int]$cfg["FF_API_PORT"]) -WebPort ([int]$cfg["FF_WEB_PORT"]) | Out-Null
Done "Whole system checked."

Say "`n== SECURITY SETTINGS ARE ON ==" Green
Say "Next sign-in: open Krov WorkAgent, sign in with your new password, and set up two-step sign-in"
Say "(about a minute; save the recovery codes it shows)."
if ($diskNote -notmatch "FullyEncrypted|On") {
    Say "Still to do yourself: turn on disk encryption. Windows Settings > Privacy & security > Device encryption" Yellow
    Say "(or BitLocker on Windows Pro). It protects the database and Docker's disk if this computer is lost." Yellow
}
if ($showKey) {
    Say "`nYour BACKUP KEY (needed to open backups if this computer is ever lost). Save it in your" Yellow
    Say "password manager now; it will not be shown again:" Yellow
    Say "    $backupKey" White
}
$backupKey = $null

<#
.SYNOPSIS  Set a new password for a FlowForge user (for example to rotate the temporary admin password).
.DESCRIPTION
    Prompts twice with hidden input. The password is hashed inside the API container
    (same Argon2 hasher the app uses) and passed over stdin, never on a command line.
.EXAMPLE   .\scripts\production\Set-FlowForgeAdminPassword.ps1 -Email you@example.com
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Email,
    [string]$TenantSlug = "flowforge-production",
    [string]$Project = "flowforge"
)
. (Join-Path $PSScriptRoot "FlowForge.Common.ps1")

function Read-Plain([string]$Prompt) {
    $secure = Read-Host $Prompt -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

$first = Read-Plain "New password for $Email"
$second = Read-Plain "Repeat new password"
if ($first -ne $second) { throw "Passwords do not match." }
if ($first.Length -lt 12) { throw "Use at least 12 characters." }
$second = $null

$api = Get-FFContainer $Project "api"
$db = Get-FFContainer $Project "db"
$hash = ($first | docker exec -i $api python -c "import sys; from flowforge.core.security import hash_password; print(hash_password(sys.stdin.readline().rstrip('\r\n')))").Trim()
$first = $null
if ($LASTEXITCODE -ne 0 -or $hash -notmatch '^\$argon2[a-z]*\$[A-Za-z0-9$+/=,.-]+$') { throw "Password hashing failed." }

$emailSql = $Email.ToLowerInvariant().Replace("'", "''")
$slugSql = $TenantSlug.Replace("'", "''")
$sql = "UPDATE users SET password_hash = '$hash', updated_at = now() WHERE lower(email) = '$emailSql' AND tenant_id = (SELECT id FROM tenants WHERE slug = '$slugSql');"
$result = ($sql | docker exec -i $db psql -U flowforge_owner -d flowforge -v ON_ERROR_STOP=1 -At)
$hash = $null; $sql = $null
if ($LASTEXITCODE -ne 0) { throw "Password update failed." }
if (($result -join "") -notmatch "UPDATE 1") { throw "No matching user for $Email in $TenantSlug (nothing changed)." }
Write-Host "PASSWORD UPDATED for $Email ($TenantSlug). Existing tokens expire within 30 minutes." -ForegroundColor Green

$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$WebRoot = Join-Path $ProjectRoot "web"
$SettingsPath = Join-Path $WebRoot "src\app\settings\page.tsx"
$CssPath = Join-Path $WebRoot "src\app\globals.css"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

foreach ($Path in @($SettingsPath, $CssPath, $Python)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$env:FLOWFORGE_SETTINGS_PATH = $SettingsPath
@'
import os
import re
from pathlib import Path

path = Path(os.environ["FLOWFORGE_SETTINGS_PATH"])
text = path.read_text(encoding="utf-8")

replacement = r'''{active.key === "security" && <div className="settings-list">
  <div className="customer-security-row">
    <span><strong>Multi-factor authentication</strong><small>Additional sign-in protection for your account</small></span>
    <b className="settings-warn">Not configured</b>
  </div>
  <div className="customer-security-callout">
    Multi-factor authentication is not active in this local build. It will be enabled through Microsoft Entra ID before production launch. This screen does not claim that MFA is currently enforced.
  </div>
  <label className="settings-control-row"><span><strong>Session timeout</strong><small>End inactive sessions automatically</small></span><select defaultValue="30"><option value="15">15 minutes</option><option value="30">30 minutes</option><option value="60">60 minutes</option><option value="120">2 hours</option></select></label>
  <div className="customer-security-row">
    <span><strong>Login history</strong><small>Recent account sign-ins and security events</small></span>
    <b className="settings-muted">Available after sign-in setup</b>
  </div>
  <div className="customer-security-row">
    <span><strong>Authorized users</strong><small>People who can access this company</small></span>
    <button type="button" className="btn small" onClick={() => setActive({ key: "roles", title: "Roles & permissions", description: "Review permission bundles and separation-of-duties controls." })}>Review access</button>
  </div>
  <div className="customer-security-row">
    <span><strong>Roles & permissions</strong><small>Control what authorized users can view and change</small></span>
    <button type="button" className="btn small" onClick={() => setActive({ key: "roles", title: "Roles & permissions", description: "Review permission bundles and separation-of-duties controls." })}>Manage roles</button>
  </div>
  <div className="customer-security-row">
    <span><strong>Data isolation</strong><small>Your company's data is isolated from other organizations</small></span>
    <b className="settings-good">Protected</b>
  </div>
  <div className="settings-security-note">Data isolation is enforced by the FlowForge backend and database. It cannot be disabled from customer settings.</div>
</div>}'''

# Replace any current security panel body, including earlier editable/read-only variants.
pattern = r'\{active\.key === "security" && <div className="settings-list">.*?</div>\}'
updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
if not count:
    raise RuntimeError("The Security settings panel was not found")

# Remove customer-visible internal implementation wording if it exists elsewhere.
updated = updated.replace("Forced row-level security", "Data isolation")
updated = updated.replace("Tenant isolation at the PostgreSQL layer", "Your company's data is isolated from other organizations")
updated = updated.replace("268 tables", "Protected")

path.write_text(updated.rstrip() + "\n", encoding="utf-8")
print("UPDATED: honest customer security settings")
'@ | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Customer security settings patch failed."
}

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.customer-security-row') {
    $Css += @'

.customer-security-row{display:flex;align-items:center;gap:14px;border:1px solid var(--line);border-radius:10px;padding:14px}.customer-security-row>span{display:block;min-width:0}.customer-security-row strong,.customer-security-row small{display:block}.customer-security-row small{color:var(--muted);font-size:10px;margin-top:3px}.customer-security-row>b,.customer-security-row>.btn{margin-left:auto;white-space:nowrap}.customer-security-callout{padding:12px 14px;border-radius:10px;background:#fff8e8;color:#80530a;font-size:10px;line-height:1.55}.settings-muted{color:var(--muted);font-size:10px}@media(max-width:620px){.customer-security-row{align-items:flex-start;flex-direction:column}.customer-security-row>b,.customer-security-row>.btn{margin-left:0}}
'@
}
[System.IO.File]::WriteAllText($CssPath, $Css, [System.Text.UTF8Encoding]::new($false))

Push-Location $WebRoot
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Customer security TypeScript validation failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Customer security production build failed." }
}
finally {
    Pop-Location
}

Write-Host "FLOWFORGE CUSTOMER SECURITY SETTINGS PASSED" -ForegroundColor Green

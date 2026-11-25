$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$Page = Join-Path $Web "src\app\payroll\page.tsx"
$Css = Join-Path $Web "src\app\globals.css"

foreach ($Path in @($Page, $Css)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$env:FLOWFORGE_PAYROLL_PAGE = $Page
@'
import os
import re
from pathlib import Path

path = Path(os.environ["FLOWFORGE_PAYROLL_PAGE"])
text = path.read_text(encoding="utf-8")

replacement = '''<section className="payroll-summary-grid">
        <article className="payroll-summary-card">
          <span>Current gross payroll</span>
          <strong>{money.format(latest.gross)}</strong>
          <small>{latest.period}</small>
        </article>
        <article className="payroll-summary-card">
          <span>Net payroll</span>
          <strong>{money.format(latest.net)}</strong>
          <small>{latest.employees} workers</small>
        </article>
        <article className="payroll-summary-card">
          <span>Payroll taxes</span>
          <strong>{money.format(latest.taxes)}</strong>
          <small>Employee and employer</small>
        </article>
        <article className="payroll-summary-card">
          <span>Open exceptions</span>
          <strong>{latest.exceptions}</strong>
          <small>Review before approval</small>
        </article>
      </section>'''

pattern = r'<section className="metrics payroll-metrics">.*?</section>'
updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
if not count:
    raise RuntimeError("Payroll metrics section was not found")

path.write_text(updated.rstrip() + "\n", encoding="utf-8")
print("REPLACED: payroll summary metrics")
'@ | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Payroll metrics markup repair failed."
}

$Styles = Get-Content -LiteralPath $Css -Raw
if ($Styles -notmatch '\.payroll-summary-grid') {
$Styles += @'

.payroll-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:0 0 16px}.payroll-summary-card{min-width:0;background:white;border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:0 8px 26px #17203308}.payroll-summary-card>span,.payroll-summary-card>strong,.payroll-summary-card>small{display:block}.payroll-summary-card>span{min-height:17px;color:var(--muted);font-size:10px;font-weight:750;line-height:1.35}.payroll-summary-card>strong{margin-top:8px;color:var(--text);font-size:24px;line-height:1.08;letter-spacing:-.03em;white-space:nowrap}.payroll-summary-card>small{min-height:15px;margin-top:8px;color:var(--muted);font-size:10px;line-height:1.45}@media(max-width:1100px){.payroll-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:620px){.payroll-summary-grid{grid-template-columns:1fr}.payroll-summary-card>strong{font-size:22px}}
'@
}

[System.IO.File]::WriteAllText(
    $Css,
    $Styles,
    [System.Text.UTF8Encoding]::new($false)
)

Push-Location $Web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Payroll metric TypeScript validation failed." }

    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Payroll metric production build failed." }
}
finally {
    Pop-Location
}

Write-Host "FLOWFORGE PAYROLL METRICS CLEANUP PASSED" -ForegroundColor Green

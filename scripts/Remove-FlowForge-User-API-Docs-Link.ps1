$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$WebRoot = Join-Path $ProjectRoot "web"
$TopbarPath = Join-Path $WebRoot "src\components\topbar.tsx"

if (-not (Test-Path -LiteralPath $TopbarPath)) {
    throw "Run this script from the FlowForge project root. Missing: $TopbarPath"
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "FlowForge virtual-environment Python was not found."
}

$env:FLOWFORGE_TOPBAR_PATH = $TopbarPath
@'
import os
import re
from pathlib import Path

path = Path(os.environ["FLOWFORGE_TOPBAR_PATH"])
text = path.read_text(encoding="utf-8")

patterns = [
    r'\s*<button[^>]*onClick=\{\(\) => window\.open\("http://127\.0\.0\.1:8000/docs".*?</button>',
    r'\s*<button[^>]*>\s*<strong>API documentation</strong>.*?</button>',
]

original = text
for pattern in patterns:
    text = re.sub(pattern, "", text, flags=re.DOTALL)

if "API documentation" in text or "127.0.0.1:8000/docs" in text:
    raise RuntimeError("The user-facing API documentation link still exists in topbar.tsx")

if text == original:
    print("API documentation link was already absent from the user topbar.")
else:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print("REMOVED: user-facing API documentation link")
'@ | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Could not remove the user-facing API documentation link."
}

Push-Location $WebRoot
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "TypeScript validation failed after removing API docs." }

    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Production build failed after removing API docs." }
}
finally {
    Pop-Location
}

Write-Host "FLOWFORGE USER API DOCS LINK REMOVED" -ForegroundColor Green

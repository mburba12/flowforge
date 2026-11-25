$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$WebSrc = Join-Path $Root "web\src"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $WebSrc)) { throw "Run from the FlowForge project root." }
if (-not (Test-Path -LiteralPath $Python)) { throw "Project Python not found: $Python" }

$env:FLOWFORGE_WEB_SRC = $WebSrc
@'
import os
import re
from pathlib import Path

root = Path(os.environ["FLOWFORGE_WEB_SRC"])
extensions = {".ts", ".tsx", ".css", ".json"}
# Common UTF-8/Windows-1252 mojibake signatures plus replacement chars.
bad_markers = ("Ã", "Â", "â", "ð", "ï¿½", "�")
changed = []
remaining = []


def score(text: str) -> int:
    return sum(text.count(marker) for marker in bad_markers)


def repair(text: str) -> str:
    current = text
    for _ in range(3):
        baseline = score(current)
        candidates = [current]
        for encoding in ("latin1", "cp1252"):
            try:
                candidates.append(current.encode(encoding).decode("utf-8"))
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        best = min(candidates, key=score)
        if score(best) >= baseline:
            break
        current = best
    # Replace encoding-sensitive punctuation with stable ASCII.
    translations = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00d7": "X",
        "\u2212": "-", "\u2022": "-", "\u00b7": "-", "\u00a0": " ",
    }
    for old, new in translations.items():
        current = current.replace(old, new)
    return current

for path in root.rglob("*"):
    if not path.is_file() or path.suffix not in extensions:
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    fixed = repair(text)
    if fixed != text:
        path.write_text(fixed, encoding="utf-8", newline="\n")
        changed.append(path)

for path in root.rglob("*"):
    if not path.is_file() or path.suffix not in extensions:
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    hits = sorted({marker for marker in bad_markers if marker in text})
    if hits:
        remaining.append((path, hits))

print(f"Repaired files: {len(changed)}")
for path in changed:
    print(f"REPAIRED: {path.relative_to(root)}")

if remaining:
    for path, hits in remaining:
        print(f"REMAINS: {path.relative_to(root)} -> {hits}")
    raise SystemExit("Mojibake remains in frontend source")

print("PASSED: no mojibake markers remain in frontend source")
'@ | & $Python -

if ($LASTEXITCODE -ne 0) { throw "Frontend encoding sanitation failed." }

# Force relevant source files to normalized UTF-8/LF via Prettier, then validate.
Push-Location (Join-Path $Root "web")
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Encoding repair TypeScript validation failed." }
    npm test
    if ($LASTEXITCODE -ne 0) { throw "Encoding repair tests failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Encoding repair build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE SITE-WIDE ENCODING REPAIR PASSED" -ForegroundColor Green

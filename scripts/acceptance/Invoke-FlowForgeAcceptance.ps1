$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
$Python = ".\.venv\Scripts\python.exe"
if ([string]::IsNullOrWhiteSpace($env:FLOWFORGE_TEST_PASSWORD)) { throw "Set FLOWFORGE_TEST_PASSWORD." }
$RunId = "{0}-{1}" -f (Get-Date -Format "yyyyMMddHHmmss"), ([guid]::NewGuid().ToString("N").Substring(0,8))
$Slug = "acceptance-$RunId"; $Email = "$Slug@example.com"; $Api = "http://127.0.0.1:8000"
& $Python -m alembic current
if ($LASTEXITCODE -ne 0) { throw "Alembic current failed." }
$body = @{tenant=@{name="FlowForge Acceptance $RunId";slug=$Slug};email=$Email;password=$env:FLOWFORGE_TEST_PASSWORD;display_name="Acceptance Owner"} | ConvertTo-Json -Depth 5
$token = Invoke-RestMethod -Method Post -Uri "$Api/api/v1/auth/bootstrap" -ContentType "application/json" -Body $body -ErrorAction Stop
if (-not $token.access_token) { throw "Bootstrap returned no token." }
$headers = @{Authorization="Bearer $($token.access_token)"}
Invoke-RestMethod -Method Get -Uri "$Api/phase1/status" -Headers $headers -ErrorAction Stop | Out-Null
Invoke-RestMethod -Method Get -Uri "$Api/phase1a/status" -Headers $headers -ErrorAction Stop | Out-Null
Invoke-RestMethod -Method Get -Uri "$Api/phase1b/health" -Headers $headers -ErrorAction Stop | Out-Null
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Backend regression failed." }
Push-Location web
try { npm run typecheck; if ($LASTEXITCODE -ne 0) { throw "Typecheck failed." }; npm test; if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed." }; npm run build; if ($LASTEXITCODE -ne 0) { throw "Build failed." }; npm run test:e2e; if ($LASTEXITCODE -ne 0) { throw "E2E failed." } } finally { Pop-Location }
Write-Host "FLOWFORGE ACCEPTANCE PASSED: $RunId" -ForegroundColor Green

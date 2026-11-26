$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run: py -3.12 -m venv .venv; .venv\Scripts\python.exe -m pip install -e .[dev]" }
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; throw "Created .env. Set real local secrets, then rerun." }
docker compose -f docker-compose.local.yml up -d
if ($LASTEXITCODE -ne 0) { throw "Local infrastructure failed." }
& $Python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw "Migration failed." }
$Api = Start-Process -FilePath $Python -ArgumentList @("-m","uvicorn","flowforge.main:app","--app-dir","src","--host","127.0.0.1","--port","8000") -PassThru
$Web = Start-Process -FilePath "npm.cmd" -ArgumentList @("run","dev") -WorkingDirectory (Join-Path $Root "web") -PassThru
@{api=$Api.Id;web=$Web.Id} | ConvertTo-Json | Set-Content ".flowforge-local-processes.json" -Encoding UTF8
Write-Host "API: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "WEB: http://localhost:3000" -ForegroundColor Green
Write-Host "MAIL: http://localhost:8025" -ForegroundColor Green

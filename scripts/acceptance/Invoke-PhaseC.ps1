[CmdletBinding()]
param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,[string]$ApiBaseUrl='http://127.0.0.1:8000',[string]$WebBaseUrl='http://127.0.0.1:3000',[switch]$SkipE2E)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest;Set-Location -LiteralPath $ProjectRoot
function Gate([string]$name,[scriptblock]$run){Write-Host "RUNNING: $name" -ForegroundColor Cyan;&$run;if($LASTEXITCODE -ne 0){throw "$name exited $LASTEXITCODE"};Write-Host "PASSED: $name" -ForegroundColor Green}
$python='.\.venv\Scripts\python.exe';if(-not(Test-Path $python)){throw '.venv Python missing'}
Gate 'Backend tests' {&$python -m pytest -q}
Push-Location '.\web';try{Gate 'Frontend install' {npm ci};Gate 'Frontend lint' {npm run lint};Gate 'Frontend typecheck' {npm run typecheck};Gate 'Frontend tests' {npm test -- --run};Gate 'Frontend production build' {npm run build}}finally{Pop-Location}
Gate 'Compose configuration' {docker compose -f docker-compose.yml -f docker-compose.phase-c.yml config --quiet}
docker compose -f docker-compose.yml -f docker-compose.phase-c.yml up -d --build;if($LASTEXITCODE -ne 0){throw 'Local stack startup failed'}
$deadline=(Get-Date).AddMinutes(3);$api=$false;$web=$false
do{try{$r=Invoke-RestMethod "$ApiBaseUrl/api/v1/health" -TimeoutSec 5;if($r.status -eq 'ok'){$api=$true}}catch{};try{$r=Invoke-WebRequest $WebBaseUrl -UseBasicParsing -TimeoutSec 5;if($r.StatusCode -eq 200){$web=$true}}catch{};if(-not($api-and$web)){Start-Sleep 2}}while((Get-Date)-lt$deadline-and-not($api-and$web))
if(-not$api){throw 'API unhealthy'};if(-not$web){throw 'Web application unavailable'}
if(-not$SkipE2E){Push-Location '.\web';try{Gate 'Browser acceptance' {npm run test:e2e}}finally{Pop-Location}}
New-Item -ItemType Directory -Force '.\var\acceptance'|Out-Null
@{phase='Phase C';status='passed';commit=(git rev-parse HEAD).Trim();completed_at=(Get-Date).ToUniversalTime().ToString('o');api=$ApiBaseUrl;web=$WebBaseUrl}|ConvertTo-Json|Set-Content '.\var\acceptance\phase-c-result.json' -Encoding UTF8
Write-Host 'FLOWFORGE PHASE C LOCAL APPLICATION ACCEPTANCE PASSED' -ForegroundColor Green
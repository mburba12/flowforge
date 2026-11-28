$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (Test-Path ".flowforge-local-processes.json") {
  $p = Get-Content ".flowforge-local-processes.json" -Raw | ConvertFrom-Json
  @($p.api,$p.web) | Where-Object { $_ } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
  Remove-Item ".flowforge-local-processes.json" -Force
}
docker compose -f docker-compose.local.yml down

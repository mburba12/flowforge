$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
docker compose `
    --env-file .\.env.recovered-database `
    -f .\docker-compose.yml `
    -f .\compose.recovered-database.yml `
    up -d
if ($LASTEXITCODE -ne 0) {
    throw "FlowForge startup failed."
}
docker compose `
    --env-file .\.env.recovered-database `
    -f .\docker-compose.yml `
    -f .\compose.recovered-database.yml `
    ps

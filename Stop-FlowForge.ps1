$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
docker compose `
    --env-file .\.env.recovered-database `
    -f .\docker-compose.yml `
    -f .\compose.recovered-database.yml `
    stop
if ($LASTEXITCODE -ne 0) {
    throw "FlowForge stop failed."
}

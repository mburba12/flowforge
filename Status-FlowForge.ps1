$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
docker compose `
    --env-file .\.env.recovered-database `
    -f .\docker-compose.yml `
    -f .\compose.recovered-database.yml `
    ps
$ApiContainer = (
    docker compose `
        --env-file .\.env.recovered-database `
        -f .\docker-compose.yml `
        -f .\compose.recovered-database.yml `
        ps -q api
).Trim()
if ($ApiContainer) {
    docker logs --tail 50 $ApiContainer
}

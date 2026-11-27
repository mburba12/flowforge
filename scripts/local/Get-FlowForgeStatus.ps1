[CmdletBinding()]
param([string]$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path)
$ErrorActionPreference="Stop"; Set-Location $ProjectRoot
docker compose ps
$Health=Invoke-RestMethod "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 15
$Ready=Invoke-RestMethod "http://127.0.0.1:8000/phase1b/health" -TimeoutSec 15
$Probe=@'
import asyncio
from sqlalchemy import text
from flowforge.db.session import engine
async def main():
    async with engine.connect() as c:
        print((await c.execute(text("select current_user,current_setting('row_security'),current_setting('is_superuser')"))).one())
    await engine.dispose()
asyncio.run(main())
'@
$Db=$Probe | docker compose exec -T api python -
if($LASTEXITCODE -ne 0){throw "Database runtime probe failed."}
[pscustomobject]@{ApiStatus=$Health.status;Phase1B=$Ready.status;Database=$Ready.database;Storage=$Ready.storage;RuntimeProbe=($Db -join " ");Revision=((docker compose exec -T postgres psql -U flowforge -d flowforge -At -c "select version_num from alembic_version;").Trim())}|Format-List

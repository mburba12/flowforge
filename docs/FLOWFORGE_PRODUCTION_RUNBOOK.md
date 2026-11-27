# FlowForge production runbook

FlowForge runs as one Docker Compose project, **`flowforge`**, defined in
`compose.production.yml`. Secrets live in `.env.production` (gitignored, generated
by `Install-FlowForge.ps1`; never commit or share it).

| Service | Purpose | Host port |
|---|---|---|
| `web` | Next.js app | `3000` |
| `api` | FastAPI, runs as the restricted role `flowforge_app` (no superuser, no RLS bypass) | `8000` |
| `db` | PostgreSQL 16, volume `flowforge_flowforge_pgdata`; forced row-level security on every tenant table | `127.0.0.1:5435` |
| `migrate` | one-shot `alembic upgrade head` as the database owner, runs before `api` starts | — |
| `redis`, `azurite`, `mailpit` | supporting services (internal only; the API does not use them yet) | — |

`docker-compose.yml` is the **isolated test stack** used by the acceptance scripts.
It is never production. Do not point acceptance scripts at the `flowforge` project.

All commands below are run from the project folder in PowerShell.

## Everyday operations

Start (or apply a new build):

```powershell
.\scripts\production\Start-FlowForge.ps1 -Build
```

Stop (data is always kept; never use `docker compose down -v`):

```powershell
.\scripts\production\Stop-FlowForge.ps1
```

Status and health:

```powershell
.\scripts\production\Status-FlowForge.ps1
```

Full read-only verification (services, migrations, RLS, runtime role, endpoints,
reference data, tenant isolation, server errors):

```powershell
.\scripts\production\Test-FlowForgeStack.ps1
```

After a Windows reboot, Docker Desktop starts the stack automatically
(`restart: unless-stopped`). If Docker Desktop is not set to start at sign-in,
start it, then run `Start-FlowForge.ps1`.

## Passwords

Rotate the administrator password (hidden prompt; hashed inside the API container):

```powershell
.\scripts\production\Set-FlowForgeAdminPassword.ps1 -Email <your sign-in email>
```

The cutover copied your existing password hash, so the temporary recovery password
still works until you run this. Run it, then delete the plaintext password line from
`release-20261127-154058\release-manifest.txt`.

## Backup and restore

Backup (verified, written to `var\backups`, gitignored):

```powershell
.\scripts\production\Backup-FlowForge.ps1 -Label daily
```

Restore into a scratch database to inspect a backup (never over production without
a fresh backup first):

```powershell
docker cp <backup.dump> flowforge-db-1:/tmp/restore.dump
docker exec flowforge-db-1 createdb -U flowforge_owner restore_check
docker exec flowforge-db-1 pg_restore -U flowforge_owner -d restore_check --no-owner /tmp/restore.dump
```

## Migrations

New schema changes are Alembic revisions under `migrations\versions`. `Start-FlowForge.ps1 -Build`
rebuilds the image and the `migrate` service applies them before the API starts.
Rehearse first with `Invoke-FlowForgeRehearsal.ps1` (disposable stack on ports 3300/8300).

## Cutover history and rollback

The live system moved from the recovered runtime (database container
`forgeflow-v4-phase0-postgres-1`, API `flowforge-phase1-api-1`, web
`flowforge-phase1-web-1`) to this stack with `Invoke-FlowForgeCutover.ps1`.
The old containers and the recovered database are **stopped, not deleted**, with
restart disabled. Records are in `var\cutover\<timestamp>\`.

To return to the old runtime:

```powershell
.\scripts\production\Rollback-FlowForgeCutover.ps1
```

Keep the recovered database for about 30 days. It also archives the legacy data that
was deliberately not imported (16 automated test-run organizations, their business
rows, and 19 legacy identity users).

## What was imported

* Tenant `flowforge-production`, its user(s), roles, role permissions, user-role
  assignments and the permission catalog (IDs preserved; password hash copied).
* 57 US jurisdictions into `tax_jurisdictions` (legacy IDs kept).
* 9 payroll import providers into `integrations_provider_definitions`
  (`data.category = payroll_import`, legacy IDs in `data.legacy_source_id`).
* 19 standard units of measure (seeded by migration `ff_seed_uom_001`).

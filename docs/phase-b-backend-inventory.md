# Phase B backend inventory

Source: commit `252e13ce113cf9352330ae2432010f5f29622400`.

- Python modules: 567
- Router modules: 53
- Service modules: 47
- Model modules: 56
- Test modules: 248
- Decorated route handlers found statically: 371
- Live OpenAPI baseline supplied by acceptance: 358 paths
- Tenant-owned tables audited by live acceptance: 682

## Architecture

The active laptop stack is FastAPI plus PostgreSQL through Docker Compose. The runtime role is `flowforge_app`; the administrative `flowforge` role is reserved for migrations, fixtures, backup, and recovery. The optional local profile already defines Redis, Azurite, and Mailpit. Azure remains adapter-only and is not required.

## Existing acceptance assets

- `Invoke-BG14.ps1`
- `Invoke-ApiTenantIsolation.ps1`
- `Invoke-FourTenantRls.ps1`
- `Invoke-BackupRestore.ps1`
- self-contained four-tenant setup and cleanup SQL

## Phase B additions

This patch adds laptop operations, migration rehearsal, controlled failure recovery, a source-derived inventory generator, operational contract tests, and an authoritative Phase B runner that composes the existing verified gates.

# Phase B scope decisions

## Closed by this package

- One-command local startup, restart, status, and safe shutdown.
- Operator backup and explicit-destination restore.
- Disposable-database migration upgrade/downgrade/re-upgrade rehearsal.
- Controlled API restart and PostgreSQL transaction rollback recovery gate.
- Runtime-role, RLS, health, static-analysis, tests, OpenAPI, tenant-isolation, backup/restore, migration, and secret-scan orchestration.
- Machine-readable Phase B acceptance report.
- Contract tests for required operational files and security invariants.

## Deliberately deferred

- Real external provider credentials and sandbox certification belong to Phase I.
- Frontend behavior belongs to Phase F.
- Azure deployment is deferred; local implementations remain primary.
- A separate worker or scheduler container is not invented because the active base Compose file exposes only `postgres` and `api`. Existing in-process/outbox behavior remains authoritative until a real worker process is introduced with domain-specific semantics.

## Runtime validation required

The package was built from the full source bundle and statically validated, but Docker/PostgreSQL acceptance must run on the Windows laptop. Phase B is complete only after `Invoke-PhaseBBackend.ps1` exits 0 there.

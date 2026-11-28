# Backend recovery

1. Stop API writes.
2. Create and checksum a custom-format PostgreSQL backup.
3. Restore first into a new database.
4. Verify Alembic revision, table count, tenant count, and forced RLS.
5. Run API tenant-isolation against the recovered environment before redirecting the application.
6. Preserve the previous database until acceptance completes.

`Invoke-BackupRestore.ps1` rehearses restore without overwriting the live database. `Invoke-MigrationRehearsal.ps1` uses a disposable database.

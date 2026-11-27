#!/bin/sh
# Runs once, on an empty data volume (postgres docker-entrypoint-initdb.d).
# Creates the restricted runtime role used by the API. Migrations run as the
# owner (POSTGRES_USER); default privileges give the runtime role DML only.
set -eu
: "${FLOWFORGE_APP_DB_PASSWORD:?FLOWFORGE_APP_DB_PASSWORD is required}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v app_password="$FLOWFORGE_APP_DB_PASSWORD" <<'SQL'
CREATE ROLE flowforge_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    PASSWORD :'app_password';
GRANT CONNECT ON DATABASE flowforge TO flowforge_app;
GRANT USAGE ON SCHEMA public TO flowforge_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO flowforge_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, USAGE, UPDATE ON SEQUENCES TO flowforge_app;
SQL
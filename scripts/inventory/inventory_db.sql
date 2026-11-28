-- Read-only database inventory. Piped to psql via stdin; emits one JSON line.
-- The session is forced read-only, so any accidental write fails.
SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;
SET statement_timeout = '120s';

WITH t AS (
    SELECT n.nspname AS s, c.relname AS t, c.oid,
           c.relrowsecurity AS rls, c.relforcerowsecurity AS force_rls
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind IN ('r', 'p')
      AND n.nspname NOT IN ('pg_catalog', 'information_schema')
      AND n.nspname NOT LIKE 'pg_toast%'
)
SELECT json_build_object(
    'server_version', current_setting('server_version'),
    'database', current_database(),
    'current_user', current_user,
    'is_superuser', (SELECT rolsuper FROM pg_roles WHERE rolname = current_user),
    'bypass_rls', (SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user),
    'alembic_versions', (
        SELECT json_agg(x.v) FROM (
            SELECT (xpath('/row/v/text()', query_to_xml(
                format('SELECT string_agg(version_num, %L) AS v FROM %I.alembic_version', ',', table_schema),
                false, true, '')))[1]::text AS v, table_schema
            FROM information_schema.tables WHERE table_name = 'alembic_version'
        ) x
    ),
    'policy_count', (SELECT count(*) FROM pg_policies),
    'roles_db', (SELECT json_agg(json_build_object('role', rolname, 'super', rolsuper, 'bypassrls', rolbypassrls, 'login', rolcanlogin))
                 FROM pg_roles WHERE rolname NOT LIKE 'pg\_%'),
    'tables', (
        SELECT json_agg(json_build_object(
            'schema', s, 'table', t, 'rls', rls, 'force_rls', force_rls,
            'rows', (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM %I.%I', s, t), false, true, '')))[1]::text::bigint,
            'column_count', (SELECT count(*) FROM pg_attribute a WHERE a.attrelid = t.oid AND a.attnum > 0 AND NOT a.attisdropped),
            'tenant_columns', (SELECT json_agg(a.attname) FROM pg_attribute a WHERE a.attrelid = t.oid AND a.attnum > 0 AND NOT a.attisdropped
                               AND a.attname IN ('tenant_id', 'organization_id', 'org_id', 'company_id')),
            'has_pk', EXISTS (SELECT 1 FROM pg_constraint k WHERE k.conrelid = t.oid AND k.contype = 'p'),
            'fk_out', (SELECT count(*) FROM pg_constraint k WHERE k.conrelid = t.oid AND k.contype = 'f'),
            'float_money_columns', (SELECT json_agg(a.attname) FROM pg_attribute a WHERE a.attrelid = t.oid AND a.attnum > 0 AND NOT a.attisdropped
                                    AND a.atttypid IN ('float4'::regtype, 'float8'::regtype)
                                    AND a.attname ~ '(amount|total|price|cost|balance|rate|tax|gross|net|pay)')
        ) ORDER BY s, t)
        FROM t
    ),
    'tenants', (SELECT json_agg(json_build_object('id', id, 'slug', slug, 'name', name, 'status', status, 'is_deleted', is_deleted) ORDER BY created_at)
                FROM public.tenants),
    'legacy_organizations', (SELECT count(*) FROM identity.organizations),
    'legacy_users', (SELECT count(*) FROM identity.users),
    'permission_catalog_public', (SELECT count(*) FROM public.permissions),
    'permission_catalog_identity', (SELECT count(*) FROM identity.permissions),
    'tenant_principals', (
        SELECT json_agg(json_build_object(
            'tenant_slug', tn.slug,
            'user_id', u.id,
            'email_masked', regexp_replace(u.email, '^(.).*(@.*)$', '\1***\2'),
            'active', u.is_active,
            'roles', (SELECT json_agg(r.name) FROM public.user_roles ur JOIN public.roles r ON r.id = ur.role_id
                      WHERE ur.user_id = u.id AND ur.tenant_id = u.tenant_id),
            'permission_count', (SELECT count(DISTINCT rp.permission_id) FROM public.user_roles ur
                                 JOIN public.role_permissions rp ON rp.role_id = ur.role_id
                                 WHERE ur.user_id = u.id AND ur.tenant_id = u.tenant_id)
        ) ORDER BY tn.slug, u.created_at)
        FROM public.users u JOIN public.tenants tn ON tn.id = u.tenant_id
    )
);

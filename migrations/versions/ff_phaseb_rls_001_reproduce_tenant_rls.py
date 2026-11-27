"""Reproduce tenant RLS on every clean database.

Revision ID: ff_phaseb_rls_001
Revises: ff_bg13_ops_001
"""

from alembic import op

revision = "ff_phaseb_rls_001"
down_revision = "ff_bg13_ops_001"
branch_labels = None
depends_on = None

_RLS_SQL = r"""
DO $flowforge_rls$
DECLARE
    r record;
    policy_name text;
    predicate text;
BEGIN
    FOR r IN
        SELECT
            n.nspname AS schema_name,
            c.relname AS table_name,
            format_type(a.atttypid, a.atttypmod) AS tenant_type
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
          AND a.attname = 'tenant_id'
          AND NOT a.attisdropped
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
            r.schema_name,
            r.table_name
        );
        EXECUTE format(
            'ALTER TABLE %I.%I FORCE ROW LEVEL SECURITY',
            r.schema_name,
            r.table_name
        );
        policy_name := left(r.table_name || '_tenant_isolation', 63);

        IF r.tenant_type = 'uuid' THEN
            predicate :=
                'tenant_id = NULLIF(' ||
                'current_setting(''app.current_tenant_id'', true), ' ||
                ''''')::uuid';
        ELSE
            predicate :=
                'tenant_id::text = NULLIF(' ||
                'current_setting(''app.current_tenant_id'', true), ' ||
                ''''')';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM pg_policy p
            JOIN pg_class pc ON pc.oid = p.polrelid
            JOIN pg_namespace pn ON pn.oid = pc.relnamespace
            WHERE pn.nspname = r.schema_name
              AND pc.relname = r.table_name
              AND p.polname = policy_name
        ) THEN
            EXECUTE format(
                'CREATE POLICY %I ON %I.%I FOR ALL USING (%s) '
                'WITH CHECK (%s)',
                policy_name,
                r.schema_name,
                r.table_name,
                predicate,
                predicate
            );
        END IF;
    END LOOP;
END
$flowforge_rls$;
"""


def upgrade() -> None:
    op.execute(_RLS_SQL)


def downgrade() -> None:
    # Security-preserving no-op: never disable tenant isolation automatically.
    pass

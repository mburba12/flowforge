"""Sign in with email only: find the workspaces an email belongs to.

users has forced row-level security, so the runtime role cannot search it across
tenants. ff_login_tenants(email) is a SECURITY DEFINER function owned by the migration
role (which bypasses RLS) that returns only tenant ids for active users of active
tenants with that email. The API calls it during sign-in and sign-up and never returns
its result without a correct password.

Revision ID: ff_login_001
Revises: ff_connect_001
"""

from alembic import op

revision = "ff_login_001"
down_revision = "ff_connect_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION ff_login_tenants(p_email text)
        RETURNS SETOF uuid
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
            SELECT u.tenant_id
            FROM public.users u
            JOIN public.tenants t ON t.id = u.tenant_id
            WHERE lower(u.email) = lower(p_email)
              AND u.is_active AND NOT u.is_deleted
              AND NOT t.is_deleted AND t.status = 'active'
            ORDER BY t.created_at
            LIMIT 20
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION ff_login_tenants(text) FROM PUBLIC")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'flowforge_app') THEN
                GRANT EXECUTE ON FUNCTION ff_login_tenants(text) TO flowforge_app;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS ff_login_tenants(text)")

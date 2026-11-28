"""Usage-based billing and per-user screen preferences.

Tables (forced tenant RLS, same-tenant triggers): billing_accounts (the card on file,
as Stripe ids only), usage_days (one row per workspace per day: storage and requests),
billing_invoices (monthly invoices and their charge state) and user_preferences
(sections a person hid).

ff_tenant_storage_bytes(): SECURITY DEFINER, callable only by the app role; returns
the bytes every workspace's rows take across all tenant tables (uploaded files included,
they are stored in the database), for the daily usage snapshot.

Revision ID: ff_billing_001
Revises: ff_login_001
"""

from alembic import op

revision = "ff_billing_001"
down_revision = "ff_login_001"
branch_labels = None
depends_on = None

_PREDICATE = "tenant_id = (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid"
_BASE = (
    "id uuid PRIMARY KEY DEFAULT gen_random_uuid(),"
    " tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,"
    " created_at timestamptz NOT NULL DEFAULT now(),"
)

TABLES = {
    "billing_accounts": """
        stripe_customer_id varchar(80),
        payment_method_id varchar(80),
        card_brand varchar(30),
        card_last4 varchar(4),
        card_exp_month integer,
        card_exp_year integer,
        authorized_at timestamptz,
        authorized_by uuid REFERENCES users(id),
        pending_checkout_session varchar(120),
        updated_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_billing_account UNIQUE (tenant_id)
    """,
    "usage_days": """
        day date NOT NULL,
        storage_bytes bigint NOT NULL DEFAULT 0,
        requests integer NOT NULL DEFAULT 0,
        bank_accounts integer NOT NULL DEFAULT 0,
        measured_at timestamptz,
        CONSTRAINT uq_usage_day UNIQUE (tenant_id, day)
    """,
    "billing_invoices": """
        number varchar(40) NOT NULL,
        period_start date NOT NULL,
        period_end date NOT NULL,
        currency varchar(3) NOT NULL DEFAULT 'usd',
        lines json NOT NULL DEFAULT '[]',
        cost_basis numeric(12,4) NOT NULL DEFAULT 0,
        total numeric(12,2) NOT NULL,
        status varchar(20) NOT NULL DEFAULT 'open',
        issued_at timestamptz NOT NULL DEFAULT now(),
        charge_on date NOT NULL,
        emailed_to varchar(1000),
        emailed_at timestamptz,
        email_error varchar(500),
        charge_attempts integer NOT NULL DEFAULT 0,
        charged_at timestamptz,
        payment_intent_id varchar(80),
        last_error varchar(500),
        CONSTRAINT uq_billing_invoice_period UNIQUE (tenant_id, period_start),
        CONSTRAINT uq_billing_invoice_number UNIQUE (tenant_id, number)
    """,
    "user_preferences": """
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        data json NOT NULL DEFAULT '{}',
        updated_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_user_preferences UNIQUE (tenant_id, user_id)
    """,
}


def upgrade() -> None:
    for table, columns in TABLES.items():
        op.execute(f"CREATE TABLE {table} ({_BASE}{columns})")
        op.execute(f"CREATE INDEX ix_{table}_tenant_id ON {table} (tenant_id)")
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table}"
            f" FOR ALL USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
        )
        op.execute(
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'flowforge_app') THEN"
            f" GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO flowforge_app;"
            " END IF; END $$"
        )
    op.execute("CREATE INDEX ix_billing_invoices_due ON billing_invoices (status, charge_on)")
    op.execute("SELECT ff_install_same_tenant_triggers()")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION ff_tenant_storage_bytes()
        RETURNS TABLE(tenant_id uuid, bytes bigint)
        LANGUAGE plpgsql
        STABLE
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE
            t record;
            parts text := '';
        BEGIN
            FOR t IN
                SELECT c.relname
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped
                WHERE n.nspname = 'public' AND c.relkind = 'r'
            LOOP
                IF parts <> '' THEN parts := parts || ' UNION ALL '; END IF;
                parts := parts || format(
                    'SELECT x.tenant_id, sum(pg_column_size(x.*))::bigint AS b FROM public.%I x GROUP BY x.tenant_id',
                    t.relname);
            END LOOP;
            IF parts = '' THEN RETURN; END IF;
            RETURN QUERY EXECUTE
                'SELECT s.tenant_id, sum(s.b)::bigint FROM (' || parts || ') s'
                || ' WHERE s.tenant_id IS NOT NULL GROUP BY s.tenant_id';
        END
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION ff_tenant_storage_bytes() FROM PUBLIC")
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'flowforge_app') THEN"
        " GRANT EXECUTE ON FUNCTION ff_tenant_storage_bytes() TO flowforge_app;"
        " END IF; END $$"
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS ff_tenant_storage_bytes()")
    for table in reversed(list(TABLES)):
        op.execute(f"DROP TABLE IF EXISTS {table}")

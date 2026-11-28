"""Uploads in every section, shipping carrier accounts and tracking, payroll migration.

Tables: attachments, carrier_accounts, tracked_shipments, payroll_migrations,
payroll_external_workers, payroll_ytd_balances. Each has forced tenant row-level
security and the same-tenant reference trigger (ff_install_same_tenant_triggers).

Revision ID: ff_connect_001
Revises: ff_security_001
"""

from alembic import op

revision = "ff_connect_001"
down_revision = "ff_security_001"
branch_labels = None
depends_on = None

_PREDICATE = "tenant_id = (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid"

_BASE = (
    "id uuid PRIMARY KEY DEFAULT gen_random_uuid(),"
    " tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,"
    " created_at timestamptz NOT NULL DEFAULT now(),"
)

TABLES = {
    "attachments": """
        section varchar(60) NOT NULL,
        record_type varchar(60),
        record_id varchar(100),
        filename varchar(255) NOT NULL,
        content_type varchar(150) NOT NULL,
        size_bytes integer NOT NULL,
        checksum varchar(64) NOT NULL,
        note varchar(500),
        content bytea NOT NULL,
        uploaded_by uuid NOT NULL REFERENCES users(id),
        is_deleted boolean NOT NULL DEFAULT false
    """,
    "carrier_accounts": """
        carrier varchar(20) NOT NULL,
        label varchar(120) NOT NULL,
        account_number_mask varchar(20),
        encrypted_credentials text NOT NULL,
        status varchar(20) NOT NULL DEFAULT 'connected',
        last_checked_at timestamptz,
        last_error varchar(500),
        connected_by uuid NOT NULL REFERENCES users(id)
    """,
    "tracked_shipments": """
        carrier varchar(20) NOT NULL,
        tracking_number varchar(60) NOT NULL,
        carrier_account_id uuid REFERENCES carrier_accounts(id) ON DELETE SET NULL,
        reference varchar(200),
        direction varchar(10) NOT NULL DEFAULT 'outbound',
        status varchar(30) NOT NULL DEFAULT 'pending',
        status_detail varchar(300),
        estimated_delivery date,
        delivered_at timestamptz,
        last_location varchar(200),
        last_event_at timestamptz,
        events json NOT NULL DEFAULT '[]',
        last_refreshed_at timestamptz,
        last_error varchar(500),
        added_by uuid NOT NULL REFERENCES users(id),
        CONSTRAINT uq_tracked_shipment UNIQUE (tenant_id, carrier, tracking_number)
    """,
    "payroll_migrations": """
        provider varchar(40) NOT NULL,
        method varchar(10) NOT NULL,
        status varchar(20) NOT NULL DEFAULT 'pending',
        company_name varchar(200),
        encrypted_tokens text,
        oauth_state varchar(80),
        filename varchar(255),
        tax_year integer,
        summary json NOT NULL DEFAULT '{}',
        errors json NOT NULL DEFAULT '[]',
        started_by uuid NOT NULL REFERENCES users(id),
        completed_at timestamptz
    """,
    "payroll_external_workers": """
        provider varchar(40) NOT NULL,
        external_id varchar(120) NOT NULL,
        worker_id uuid NOT NULL REFERENCES worker_profiles(id) ON DELETE CASCADE,
        email varchar(320),
        CONSTRAINT uq_payroll_external_worker UNIQUE (tenant_id, provider, external_id)
    """,
    "payroll_ytd_balances": """
        worker_id uuid NOT NULL REFERENCES worker_profiles(id) ON DELETE CASCADE,
        tax_year integer NOT NULL,
        gross_pay numeric(20,2) NOT NULL DEFAULT 0,
        federal_income_tax numeric(20,2) NOT NULL DEFAULT 0,
        social_security_tax numeric(20,2) NOT NULL DEFAULT 0,
        medicare_tax numeric(20,2) NOT NULL DEFAULT 0,
        state_income_tax numeric(20,2) NOT NULL DEFAULT 0,
        other_deductions numeric(20,2) NOT NULL DEFAULT 0,
        net_pay numeric(20,2) NOT NULL DEFAULT 0,
        migration_id uuid REFERENCES payroll_migrations(id) ON DELETE SET NULL,
        CONSTRAINT uq_payroll_ytd_balance UNIQUE (tenant_id, worker_id, tax_year)
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
    op.execute("CREATE INDEX ix_attachments_section ON attachments (tenant_id, section)")
    op.execute("SELECT ff_install_same_tenant_triggers()")


def downgrade() -> None:
    for table in reversed(list(TABLES)):
        op.execute(f"DROP TABLE IF EXISTS {table}")

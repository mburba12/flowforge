"""Sales order status history (append-only) with forced tenant RLS; backfill current statuses.

Revision ID: ff_release_002
Revises: ff_rbac_001
"""

from alembic import op

revision = "ff_release_002"
down_revision = "ff_rbac_001"
branch_labels = None
depends_on = None

_PREDICATE = "tenant_id = (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid"


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE sales_order_status_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            order_id uuid NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
            status varchar(40) NOT NULL,
            note varchar(300),
            changed_by uuid REFERENCES users(id),
            changed_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_sales_order_status_events_tenant_id ON sales_order_status_events (tenant_id)"
    )
    op.execute(
        "CREATE INDEX ix_sales_order_status_events_order_id ON sales_order_status_events (order_id)"
    )
    op.execute("ALTER TABLE sales_order_status_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sales_order_status_events FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY sales_order_status_events_tenant_isolation ON sales_order_status_events"
        f" FOR ALL USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
    )
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'flowforge_app') THEN"
        " GRANT SELECT, INSERT ON sales_order_status_events TO flowforge_app;"
        " REVOKE UPDATE, DELETE, TRUNCATE ON sales_order_status_events FROM flowforge_app;"
        " END IF; END $$"
    )
    op.execute(
        "INSERT INTO sales_order_status_events (tenant_id, order_id, status, note, changed_by)"
        " SELECT tenant_id, id, status, 'backfilled current status', created_by FROM sales_orders"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sales_order_status_events")

"""Per-tenant document number sequences (atomic; replaces count()+1 numbering).

Revision ID: ff_release_003
Revises: ff_release_002
"""

from alembic import op

revision = "ff_release_003"
down_revision = "ff_release_002"
branch_labels = None
depends_on = None

_PREDICATE = "tenant_id = (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid"


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE document_sequences (
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            key varchar(60) NOT NULL,
            value bigint NOT NULL,
            PRIMARY KEY (tenant_id, key)
        )
        """
    )
    op.execute("ALTER TABLE document_sequences ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE document_sequences FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY document_sequences_tenant_isolation ON document_sequences"
        f" FOR ALL USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
    )
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'flowforge_app') THEN"
        " GRANT SELECT, INSERT, UPDATE ON document_sequences TO flowforge_app;"
        " REVOKE DELETE, TRUNCATE ON document_sequences FROM flowforge_app;"
        " END IF; END $$"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_sequences")

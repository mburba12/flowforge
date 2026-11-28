"""BG-05 completion landed costs, manifests, and outbox."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ff_bg05_completion_001"
down_revision = "ff_bg05_commerce_001"
branch_labels = None
depends_on = None
TABLES = ["commerce_landed_costs", "commerce_manifests", "commerce_events_outbox"]


def b():
    return [
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]


def r(t):
    op.create_index(f"ix_{t}_tenant_id", t, ["tenant_id"])
    op.execute(sa.text(f'ALTER TABLE "{t}" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{t}" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            f'''CREATE POLICY "{t}_tenant_isolation" ON "{t}" USING (tenant_id=NULLIF(current_setting('app.current_tenant_id',true),'')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting('app.current_tenant_id',true),'')::uuid)'''
        )
    )


def upgrade():
    op.create_table(
        "commerce_landed_costs",
        *b(),
        sa.Column(
            "receipt_id", postgresql.UUID(), sa.ForeignKey("goods_receipts.id"), nullable=False
        ),
        sa.Column("cost_type", sa.String(50)),
        sa.Column("amount", sa.Numeric(20, 6)),
        sa.Column("allocation_method", sa.String(30)),
        sa.Column("status", sa.String(30), server_default="draft"),
    )
    op.create_table(
        "commerce_manifests",
        *b(),
        sa.Column("manifest_number", sa.String(100)),
        sa.Column("carrier_code", sa.String(40)),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("shipment_ids_json", sa.Text(), server_default="[]"),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "manifest_number", name="uq_manifest_number"),
    )
    op.create_table(
        "commerce_events_outbox",
        *b(),
        sa.Column("event_type", sa.String(100)),
        sa.Column("aggregate_type", sa.String(60)),
        sa.Column("aggregate_id", postgresql.UUID()),
        sa.Column("payload_json", sa.Text()),
        sa.Column("status", sa.String(30), server_default="pending"),
        sa.Column("attempts", sa.Integer(), server_default="0"),
    )
    for t in TABLES:
        r(t)


def downgrade():
    for t in reversed(TABLES):
        op.execute(sa.text(f'DROP POLICY IF EXISTS "{t}_tenant_isolation" ON "{t}"'))
        op.drop_table(t)

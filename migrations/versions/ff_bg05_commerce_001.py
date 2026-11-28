"""Complete BG-05 commerce, inventory, and shipping backend."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ff_bg05_commerce_001"
down_revision = "ff_bg04_completion_001"
branch_labels = None
depends_on = None
TABLES = [
    "commerce_requisitions_final",
    "commerce_requisition_lines_final",
    "commerce_inventory_lots_final",
    "commerce_inventory_serials_final",
    "commerce_inventory_transfers_final",
    "commerce_inventory_counts_final",
    "commerce_inventory_count_lines_final",
    "commerce_returns_final",
    "commerce_shipping_rates_final",
    "commerce_shipping_labels_final",
    "commerce_tracking_events_final",
    "commerce_shipping_claims_final",
    "commerce_executions_final",
]


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
        sa.Column("version", sa.Integer(), server_default="1"),
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
        "commerce_requisitions_final",
        *b(),
        sa.Column("number", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("requester_id", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("needed_on", sa.Date()),
        sa.Column("total_amount", sa.Numeric(20, 6), server_default="0"),
        sa.Column("approved_by", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.Column("converted_po_id", postgresql.UUID(), sa.ForeignKey("purchase_orders.id")),
        sa.UniqueConstraint("tenant_id", "number", name="uq_requisition_number"),
    )
    op.create_table(
        "commerce_requisition_lines_final",
        *b(),
        sa.Column(
            "requisition_id",
            postgresql.UUID(),
            sa.ForeignKey("commerce_requisitions_final.id", ondelete="CASCADE"),
        ),
        sa.Column("product_id", postgresql.UUID(), sa.ForeignKey("products.id")),
        sa.Column("description", sa.String(500)),
        sa.Column("quantity", sa.Numeric(20, 6)),
        sa.Column("unit_price", sa.Numeric(20, 6)),
        sa.Column("line_total", sa.Numeric(20, 6)),
    )
    op.create_table(
        "commerce_inventory_lots_final",
        *b(),
        sa.Column("product_id", postgresql.UUID(), sa.ForeignKey("products.id")),
        sa.Column("lot_number", sa.String(120)),
        sa.Column("expiration_date", sa.Date()),
        sa.Column("status", sa.String(30), server_default="available"),
        sa.UniqueConstraint("tenant_id", "product_id", "lot_number", name="uq_inventory_lot"),
    )
    op.create_table(
        "commerce_inventory_serials_final",
        *b(),
        sa.Column("product_id", postgresql.UUID(), sa.ForeignKey("products.id")),
        sa.Column("serial_number", sa.String(160)),
        sa.Column("warehouse_id", postgresql.UUID(), sa.ForeignKey("warehouses.id")),
        sa.Column("status", sa.String(30), server_default="available"),
        sa.UniqueConstraint("tenant_id", "serial_number", name="uq_inventory_serial"),
    )
    op.create_table(
        "commerce_inventory_transfers_final",
        *b(),
        sa.Column("number", sa.String(80)),
        sa.Column("product_id", postgresql.UUID(), sa.ForeignKey("products.id")),
        sa.Column("source_warehouse_id", postgresql.UUID(), sa.ForeignKey("warehouses.id")),
        sa.Column("target_warehouse_id", postgresql.UUID(), sa.ForeignKey("warehouses.id")),
        sa.Column("quantity", sa.Numeric(20, 6)),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("approved_by", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.UniqueConstraint("tenant_id", "number", name="uq_inventory_transfer"),
    )
    op.create_table(
        "commerce_inventory_counts_final",
        *b(),
        sa.Column("number", sa.String(80)),
        sa.Column("warehouse_id", postgresql.UUID(), sa.ForeignKey("warehouses.id")),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("counted_by", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.Column("approved_by", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.UniqueConstraint("tenant_id", "number", name="uq_inventory_count"),
    )
    op.create_table(
        "commerce_inventory_count_lines_final",
        *b(),
        sa.Column(
            "count_id",
            postgresql.UUID(),
            sa.ForeignKey("commerce_inventory_counts_final.id", ondelete="CASCADE"),
        ),
        sa.Column("product_id", postgresql.UUID(), sa.ForeignKey("products.id")),
        sa.Column("location_id", postgresql.UUID(), sa.ForeignKey("warehouse_locations.id")),
        sa.Column("system_quantity", sa.Numeric(20, 6)),
        sa.Column("counted_quantity", sa.Numeric(20, 6)),
        sa.Column("variance", sa.Numeric(20, 6)),
    )
    op.create_table(
        "commerce_returns_final",
        *b(),
        sa.Column("number", sa.String(80)),
        sa.Column("order_id", postgresql.UUID(), sa.ForeignKey("sales_orders.id")),
        sa.Column("status", sa.String(30), server_default="requested"),
        sa.Column("reason", sa.String(200)),
        sa.Column("refund_amount", sa.Numeric(20, 6), server_default="0"),
        sa.Column("received_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "number", name="uq_return_number"),
    )
    op.create_table(
        "commerce_shipping_rates_final",
        *b(),
        sa.Column("shipment_reference", sa.String(120)),
        sa.Column("carrier_code", sa.String(40)),
        sa.Column("service_code", sa.String(80)),
        sa.Column("amount", sa.Numeric(20, 6)),
        sa.Column("currency_code", sa.String(3)),
        sa.Column("estimated_days", sa.Integer()),
        sa.Column("selected", sa.Boolean(), server_default=sa.false()),
    )
    op.create_table(
        "commerce_shipping_labels_final",
        *b(),
        sa.Column("shipment_id", postgresql.UUID(), sa.ForeignKey("shipments.id")),
        sa.Column("carrier_code", sa.String(40)),
        sa.Column("service_code", sa.String(80)),
        sa.Column("tracking_number_mask", sa.String(120)),
        sa.Column("status", sa.String(30), server_default="simulated"),
        sa.Column("document_reference", sa.String(500)),
        sa.Column("idempotency_key", sa.String(160)),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_shipping_label_idem"),
    )
    op.create_table(
        "commerce_tracking_events_final",
        *b(),
        sa.Column("shipment_id", postgresql.UUID(), sa.ForeignKey("shipments.id")),
        sa.Column("event_code", sa.String(80)),
        sa.Column("description", sa.String(500)),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
        sa.Column("location_text", sa.String(300)),
    )
    op.create_table(
        "commerce_shipping_claims_final",
        *b(),
        sa.Column("shipment_id", postgresql.UUID(), sa.ForeignKey("shipments.id")),
        sa.Column("claim_number", sa.String(100)),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("reason", sa.String(200)),
        sa.Column("amount", sa.Numeric(20, 6), server_default="0"),
        sa.Column("evidence_json", sa.Text(), server_default="{}"),
        sa.UniqueConstraint("tenant_id", "claim_number", name="uq_shipping_claim"),
    )
    op.create_table(
        "commerce_executions_final",
        *b(),
        sa.Column("operation", sa.String(80)),
        sa.Column("idempotency_key", sa.String(160)),
        sa.Column("aggregate_type", sa.String(60)),
        sa.Column("aggregate_id", postgresql.UUID()),
        sa.Column("result_json", sa.Text(), server_default="{}"),
        sa.UniqueConstraint(
            "tenant_id", "operation", "idempotency_key", name="uq_commerce_execution"
        ),
    )
    for t in TABLES:
        r(t)


def downgrade():
    for t in reversed(TABLES):
        op.execute(sa.text(f'DROP POLICY IF EXISTS "{t}_tenant_isolation" ON "{t}"'))
        op.drop_table(t)

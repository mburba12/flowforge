"""BG-08 final integration completion."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ff_bg08_completion_001"
down_revision = "ff_bg08_final_001"
branch_labels = None
depends_on = None
TABLES = [
    "billing_subscription_amendments_final",
    "billing_run_items_final",
    "project_billing_runs_final",
    "bg08_executions_final",
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
        "billing_subscription_amendments_final",
        *b(),
        sa.Column(
            "subscription_id", postgresql.UUID(), sa.ForeignKey("billing_subscriptions_final.id")
        ),
        sa.Column("amendment_type", sa.String(40)),
        sa.Column("effective_date", sa.Date()),
        sa.Column("old_quantity", sa.Numeric(20, 6)),
        sa.Column("new_quantity", sa.Numeric(20, 6)),
        sa.Column("proration_amount", sa.Numeric(20, 6)),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("approved_by", postgresql.UUID(), sa.ForeignKey("users.id")),
    )
    op.create_table(
        "billing_run_items_final",
        *b(),
        sa.Column(
            "billing_run_id",
            postgresql.UUID(),
            sa.ForeignKey("billing_runs_final.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "subscription_id", postgresql.UUID(), sa.ForeignKey("billing_subscriptions_final.id")
        ),
        sa.Column("amount", sa.Numeric(20, 6)),
        sa.Column("status", sa.String(30), server_default="calculated"),
        sa.Column("invoice_id", postgresql.UUID(), sa.ForeignKey("customer_invoices.id")),
        sa.UniqueConstraint(
            "tenant_id", "billing_run_id", "subscription_id", name="uq_billing_run_subscription"
        ),
    )
    op.create_table(
        "project_billing_runs_final",
        *b(),
        sa.Column("project_id", postgresql.UUID(), sa.ForeignKey("projects_final.id")),
        sa.Column("period_start", sa.Date()),
        sa.Column("period_end", sa.Date()),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("billable_time", sa.Numeric(20, 6), server_default="0"),
        sa.Column("billable_expenses", sa.Numeric(20, 6), server_default="0"),
        sa.Column("invoice_id", postgresql.UUID(), sa.ForeignKey("customer_invoices.id")),
        sa.Column("revenue_recognized", sa.Numeric(20, 6), server_default="0"),
    )
    op.create_table(
        "bg08_executions_final",
        *b(),
        sa.Column("operation", sa.String(80)),
        sa.Column("idempotency_key", sa.String(160)),
        sa.Column("aggregate_type", sa.String(60)),
        sa.Column("aggregate_id", postgresql.UUID()),
        sa.Column("result_json", sa.Text(), server_default="{}"),
        sa.Column("actor_user_id", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.UniqueConstraint("tenant_id", "operation", "idempotency_key", name="uq_bg08_execution"),
    )
    for t in TABLES:
        r(t)


def downgrade():
    for t in reversed(TABLES):
        op.execute(sa.text(f'DROP POLICY IF EXISTS "{t}_tenant_isolation" ON "{t}"'))
        op.drop_table(t)

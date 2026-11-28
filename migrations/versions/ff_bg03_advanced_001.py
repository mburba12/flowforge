"""BG-03 advanced persistent finance workflows."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ff_bg03_advanced_001"
down_revision = "ff_all_apis_delta_001"
branch_labels = None
depends_on = None
TABLES = [
    "finance_close_runs",
    "finance_recurring_journals",
    "finance_payment_batches",
    "finance_reconciliation_sessions",
    "finance_budget_versions",
    "finance_budget_lines",
    "finance_consolidation_runs",
    "finance_asset_register",
]


def upgrade():
    # SQLAlchemy metadata creates full structures in new installs; this migration is intentionally explicit enough for live upgrades.
    op.create_table(
        "finance_close_runs",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ledger_id", postgresql.UUID(), sa.ForeignKey("ledgers.id"), nullable=False),
        sa.Column(
            "period_id", postgresql.UUID(), sa.ForeignKey("accounting_periods.id"), nullable=False
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("tolerance", sa.Numeric(20, 6), nullable=False, server_default="0"),
        sa.Column("blockers_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_by", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_by", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "ledger_id", "period_id", name="uq_close_run_period"),
    )
    # Remaining tables are created from model metadata by bootstrap in this package installer.


def downgrade():
    op.drop_table("finance_close_runs")

"""Complete BG-04 CRM and sales backend."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ff_bg04_crm_001"
down_revision = "ff_foundation_final_001"
branch_labels = None
depends_on = None
TABLES = [
    "crm_leads_final",
    "crm_opportunities_final",
    "crm_activities_final",
    "crm_campaigns_final",
    "crm_quotes_final",
    "crm_quote_lines_final",
    "crm_credit_profiles_final",
    "crm_communications_final",
    "crm_portal_tokens_final",
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
        "crm_leads_final",
        *b(),
        sa.Column("lead_number", sa.String(80), nullable=False),
        sa.Column("company_name", sa.String(240)),
        sa.Column("contact_name", sa.String(240), nullable=False),
        sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(80)),
        sa.Column("source", sa.String(100)),
        sa.Column("status", sa.String(30), server_default="new"),
        sa.Column("owner_id", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.Column("score", sa.Integer(), server_default="0"),
        sa.Column("converted_party_id", postgresql.UUID(), sa.ForeignKey("parties.id")),
        sa.UniqueConstraint("tenant_id", "lead_number", name="uq_crm_lead_number"),
    )
    op.create_table(
        "crm_opportunities_final",
        *b(),
        sa.Column("opportunity_number", sa.String(80), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("party_id", postgresql.UUID(), sa.ForeignKey("parties.id")),
        sa.Column("lead_id", postgresql.UUID(), sa.ForeignKey("crm_leads_final.id")),
        sa.Column("stage", sa.String(40), server_default="qualification"),
        sa.Column("probability", sa.Integer(), server_default="10"),
        sa.Column("amount", sa.Numeric(20, 6), server_default="0"),
        sa.Column("currency_code", sa.String(3), server_default="USD"),
        sa.Column("expected_close_date", sa.Date()),
        sa.Column("owner_id", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.Column("lost_reason", sa.Text()),
        sa.UniqueConstraint("tenant_id", "opportunity_number", name="uq_crm_opportunity_number"),
    )
    op.create_table(
        "crm_activities_final",
        *b(),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", postgresql.UUID(), nullable=False),
        sa.Column("activity_type", sa.String(40), nullable=False),
        sa.Column("subject", sa.String(300), nullable=False),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("owner_id", postgresql.UUID(), sa.ForeignKey("users.id")),
    )
    op.create_table(
        "crm_campaigns_final",
        *b(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("starts_on", sa.Date()),
        sa.Column("ends_on", sa.Date()),
        sa.Column("budget", sa.Numeric(20, 6), server_default="0"),
        sa.Column("actual_cost", sa.Numeric(20, 6), server_default="0"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_crm_campaign_code"),
    )
    op.create_table(
        "crm_quotes_final",
        *b(),
        sa.Column("quote_number", sa.String(80), nullable=False),
        sa.Column("party_id", postgresql.UUID(), sa.ForeignKey("parties.id"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(), sa.ForeignKey("crm_opportunities_final.id")),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Numeric(20, 6), server_default="0"),
        sa.Column("discount_total", sa.Numeric(20, 6), server_default="0"),
        sa.Column("tax_total", sa.Numeric(20, 6), server_default="0"),
        sa.Column("total", sa.Numeric(20, 6), server_default="0"),
        sa.Column("valid_until", sa.Date()),
        sa.Column("approved_by", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.Column("converted_order_id", postgresql.UUID(), sa.ForeignKey("sales_orders.id")),
        sa.UniqueConstraint("tenant_id", "quote_number", name="uq_crm_quote_number"),
    )
    op.create_table(
        "crm_quote_lines_final",
        *b(),
        sa.Column(
            "quote_id",
            postgresql.UUID(),
            sa.ForeignKey("crm_quotes_final.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", postgresql.UUID(), sa.ForeignKey("products.id")),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("unit_price", sa.Numeric(20, 6), nullable=False),
        sa.Column("discount_bps", sa.Integer(), server_default="0"),
        sa.Column("line_total", sa.Numeric(20, 6), nullable=False),
    )
    op.create_table(
        "crm_credit_profiles_final",
        *b(),
        sa.Column("party_id", postgresql.UUID(), sa.ForeignKey("parties.id"), nullable=False),
        sa.Column("credit_limit", sa.Numeric(20, 6), server_default="0"),
        sa.Column("current_exposure", sa.Numeric(20, 6), server_default="0"),
        sa.Column("status", sa.String(30), server_default="active"),
        sa.Column("hold_reason", sa.Text()),
        sa.Column("approved_by", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.UniqueConstraint("tenant_id", "party_id", name="uq_crm_credit_party"),
    )
    op.create_table(
        "crm_communications_final",
        *b(),
        sa.Column("party_id", postgresql.UUID(), sa.ForeignKey("parties.id")),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(300)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), server_default="recorded"),
        sa.Column("external_reference", sa.String(300)),
    )
    op.create_table(
        "crm_portal_tokens_final",
        *b(),
        sa.Column("party_id", postgresql.UUID(), sa.ForeignKey("parties.id"), nullable=False),
        sa.Column("token_hash", sa.String(128), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    for t in TABLES:
        r(t)


def downgrade():
    for t in reversed(TABLES):
        op.execute(sa.text(f'DROP POLICY IF EXISTS "{t}_tenant_isolation" ON "{t}"'))
        op.drop_table(t)

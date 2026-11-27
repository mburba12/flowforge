"""BG-06 ultimate gap closure."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ff_bg06_ultimate_001"
down_revision = "ff_bg06_completion_001"
branch_labels = None
depends_on = None
TABLES = [
    "workforce_interviews_final",
    "workforce_onboarding_templates_final",
    "workforce_review_templates_final",
    "workforce_benefit_dependents_final",
    "workforce_clock_events_final",
    "workforce_payroll_transfers_final",
    "workforce_report_runs_final",
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
        "workforce_interviews_final",
        *b(),
        sa.Column(
            "application_id", postgresql.UUID(), sa.ForeignKey("workforce_applications_final.id")
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("panel_json", sa.Text(), server_default="[]"),
        sa.Column("scorecard_json", sa.Text(), server_default="{}"),
        sa.Column("status", sa.String(30), server_default="scheduled"),
    )
    op.create_table(
        "workforce_onboarding_templates_final",
        *b(),
        sa.Column("code", sa.String(80)),
        sa.Column("name", sa.String(200)),
        sa.Column("tasks_json", sa.Text()),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_onboarding_template"),
    )
    op.create_table(
        "workforce_review_templates_final",
        *b(),
        sa.Column("code", sa.String(80)),
        sa.Column("name", sa.String(200)),
        sa.Column("competencies_json", sa.Text()),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_review_template"),
    )
    op.create_table(
        "workforce_benefit_dependents_final",
        *b(),
        sa.Column("worker_id", postgresql.UUID(), sa.ForeignKey("worker_profiles.id")),
        sa.Column("name", sa.String(240)),
        sa.Column("relationship", sa.String(60)),
        sa.Column("encrypted_identifier", sa.Text()),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
    )
    op.create_table(
        "workforce_clock_events_final",
        *b(),
        sa.Column("worker_id", postgresql.UUID(), sa.ForeignKey("worker_profiles.id")),
        sa.Column("event_type", sa.String(30)),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
        sa.Column("timezone", sa.String(80)),
        sa.Column("source", sa.String(40)),
        sa.Column("idempotency_key", sa.String(160)),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_clock_event_idem"),
    )
    op.create_table(
        "workforce_payroll_transfers_final",
        *b(),
        sa.Column("worker_id", postgresql.UUID(), sa.ForeignKey("worker_profiles.id")),
        sa.Column("source_type", sa.String(40)),
        sa.Column("source_id", postgresql.UUID()),
        sa.Column("status", sa.String(30), server_default="queued"),
        sa.Column("idempotency_key", sa.String(160)),
        sa.Column("payload_json", sa.Text()),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_workforce_payroll_transfer"),
    )
    op.create_table(
        "workforce_report_runs_final",
        *b(),
        sa.Column("report_code", sa.String(80)),
        sa.Column("parameters_json", sa.Text(), server_default="{}"),
        sa.Column("status", sa.String(30), server_default="completed"),
        sa.Column("result_json", sa.Text(), server_default="{}"),
        sa.Column("requested_by", postgresql.UUID(), sa.ForeignKey("users.id")),
    )
    for t in TABLES:
        r(t)


def downgrade():
    for t in reversed(TABLES):
        op.execute(sa.text(f'DROP POLICY IF EXISTS "{t}_tenant_isolation" ON "{t}"'))
        op.drop_table(t)

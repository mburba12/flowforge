"""BG-00/01/02 completion persistence."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ff_foundation_completion_001"
down_revision = "ff_bg03_completion_001"
branch_labels = None
depends_on = None
TENANT = [
    "foundation_module_entitlements",
    "foundation_access_reviews",
    "foundation_support_grants",
    "master_data_stewardship_tasks",
    "master_data_quality_rules",
    "master_data_quality_issues",
    "master_data_export_jobs",
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
        "foundation_module_entitlements",
        *b(),
        sa.Column("module_code", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), server_default="enabled"),
        sa.Column("dependencies_json", sa.Text(), server_default="[]"),
        sa.Column("effective_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "module_code", name="uq_foundation_entitlement"),
    )
    op.create_table(
        "foundation_access_reviews",
        *b(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("scope_json", sa.Text(), server_default="{}"),
        sa.Column("reviewer_id", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision_json", sa.Text(), server_default="{}"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "foundation_support_grants",
        *b(),
        sa.Column("support_user_id", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scope_json", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_table(
        "master_data_stewardship_tasks",
        *b(),
        sa.Column("party_id", postgresql.UUID(), sa.ForeignKey("parties.id")),
        sa.Column("task_type", sa.String(60), nullable=False),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("assigned_to", postgresql.UUID(), sa.ForeignKey("users.id")),
        sa.Column("priority", sa.Integer(), server_default="3"),
        sa.Column("details_json", sa.Text(), server_default="{}"),
        sa.Column("resolution", sa.Text()),
    )
    op.create_table(
        "master_data_quality_rules",
        *b(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("rule_type", sa.String(40), nullable=False),
        sa.Column("configuration_json", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_mdq_rule"),
    )
    op.create_table(
        "master_data_quality_issues",
        *b(),
        sa.Column(
            "rule_id",
            postgresql.UUID(),
            sa.ForeignKey("master_data_quality_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_id", postgresql.UUID(), nullable=False),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("details_json", sa.Text(), server_default="{}"),
        sa.Column("resolved_by", postgresql.UUID(), sa.ForeignKey("users.id")),
    )
    op.create_table(
        "master_data_export_jobs",
        *b(),
        sa.Column("job_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), server_default="queued"),
        sa.Column("cursor", sa.String(250)),
        sa.Column("format", sa.String(20), server_default="jsonl"),
        sa.Column("result_reference", sa.String(500)),
        sa.Column("requested_by", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_table(
        "foundation_requirement_evidence",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("requirement_id", sa.String(80), nullable=False),
        sa.Column("artifact_path", sa.String(500), nullable=False),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending"),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.UniqueConstraint(
            "requirement_id", "artifact_path", "evidence_type", name="uq_requirement_evidence"
        ),
    )
    for t in TENANT:
        r(t)


def downgrade():
    op.drop_table("foundation_requirement_evidence")
    for t in reversed(TENANT):
        op.execute(sa.text(f'DROP POLICY IF EXISTS "{t}_tenant_isolation" ON "{t}"'))
        op.drop_table(t)

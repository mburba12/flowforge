from alembic import op

import flowforge.bg10_final.models  # noqa: F401
from flowforge.db.base import Base

revision = "ff_bg10_001"
down_revision = "ff_bg09_001"
branch_labels = None
depends_on = None
NAMES = ["bg10_information_records", "bg10_copilot_proposals"]


def upgrade():
    bind = op.get_bind()
    for name in NAMES:
        Base.metadata.tables[name].create(bind, checkfirst=True)
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f"CREATE POLICY {name}_tenant_isolation ON \"{name}\" USING (tenant_id=NULLIF(current_setting('app.current_tenant_id',true),'')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting('app.current_tenant_id',true),'')::uuid)"
        )


def downgrade():
    for name in reversed(NAMES):
        op.drop_table(name)

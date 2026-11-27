from alembic import op
from flowforge.db.base import Base
import flowforge.bg09_final.models  # noqa: F401
revision='ff_bg09_001'
down_revision='ff_bg08_completion_001'
branch_labels=None
depends_on=None
NAMES=['bg09_manufacturing_records', 'bg09_genealogy_edges']
def upgrade():
 bind=op.get_bind()
 for name in NAMES:
  Base.metadata.tables[name].create(bind,checkfirst=True)
  op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
  op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
  op.execute(f"CREATE POLICY {name}_tenant_isolation ON \"{name}\" USING (tenant_id=NULLIF(current_setting(\'app.current_tenant_id\',true),\'\')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(\'app.current_tenant_id\',true),\'\')::uuid)")
def downgrade():
 for name in reversed(NAMES): op.drop_table(name)

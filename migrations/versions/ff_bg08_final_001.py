"""BG-08 billing projects assets.

Revision uses ORM metadata tables registered by bg08_final models.
"""
from alembic import op
from flowforge.db.base import Base
import flowforge.platform.models  # noqa: F401
import flowforge.phase2a.models  # noqa: F401
import flowforge.phase2b.models  # noqa: F401
import flowforge.phase3b.models  # noqa: F401
import flowforge.finance_advanced.models  # noqa: F401
import flowforge.bg08_final.models  # noqa: F401
revision="ff_bg08_final_001"
down_revision="ff_bg07_completion_001"
branch_labels=None
depends_on=None
NAMES=["billing_plans_final","billing_subscriptions_final","billing_entitlements_final","billing_usage_records_final","billing_runs_final","billing_dunning_cases_final","projects_final","project_tasks_final","project_time_final","project_expenses_final","project_change_orders_final","asset_books_final","asset_transactions_final","bg08_events_outbox"]
def upgrade():
 bind=op.get_bind()
 for name in NAMES:
  Base.metadata.tables[name].create(bind,checkfirst=True)
  op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
  op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
  op.execute(f"CREATE POLICY {name}_tenant_isolation ON \"{name}\" USING (tenant_id=NULLIF(current_setting(\'app.current_tenant_id\',true),\'\')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(\'app.current_tenant_id\',true),\'\')::uuid)")
def downgrade():
 for name in reversed(NAMES): op.drop_table(name)

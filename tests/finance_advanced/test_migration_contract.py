from pathlib import Path
import ast

def test_advanced_migrations_create_all_tables():
 root=Path('migrations/versions'); text=(root/'ff_bg03_advanced_001.py').read_text()+(root/'ff_bg03_advanced_002.py').read_text()
 required={'finance_close_runs','finance_recurring_journals','finance_payment_batches','finance_reconciliation_sessions','finance_budget_versions','finance_budget_lines','finance_consolidation_runs','finance_asset_register'}
 assert all(f"op.create_table('{x}'" in text for x in required)
 assert 'ENABLE ROW LEVEL SECURITY' in text and 'FORCE ROW LEVEL SECURITY' in text

def test_migration_syntax():
 for name in ('ff_bg03_advanced_001.py','ff_bg03_advanced_002.py'): ast.parse((Path('migrations/versions')/name).read_text())

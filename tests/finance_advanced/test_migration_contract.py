import ast
from pathlib import Path


def created_tables(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    tables: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        function = node.func

        if not (
            isinstance(function, ast.Attribute)
            and function.attr == "create_table"
            and isinstance(function.value, ast.Name)
            and function.value.id == "op"
        ):
            continue

        if not node.args:
            continue

        table_name = node.args[0]

        if isinstance(table_name, ast.Constant) and isinstance(table_name.value, str):
            tables.add(table_name.value)

    return tables


def test_advanced_migrations_create_all_tables() -> None:
    root = Path("migrations/versions")

    tables = created_tables(root / "ff_bg03_advanced_001.py") | created_tables(
        root / "ff_bg03_advanced_002.py"
    )

    required = {
        "finance_close_runs",
        "finance_recurring_journals",
        "finance_payment_batches",
        "finance_reconciliation_sessions",
        "finance_budget_versions",
        "finance_budget_lines",
        "finance_consolidation_runs",
        "finance_asset_register",
    }

    assert required <= tables

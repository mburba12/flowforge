from flowforge.db.base import Base
from flowforge.phase4e import models  # noqa: F401

EXPECTED = {
    "operational_scorecards",
    "reconciliation_exceptions",
    "reconciliation_items",
    "reconciliation_definitions",
    "reconciliation_runs",
    "operational_metrics",
    "reconciliation_matches",
    "reconciliation_resolutions",
}


def test_tables() -> None:
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns

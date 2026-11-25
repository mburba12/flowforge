from flowforge.db.base import Base
from flowforge.phase4j import models  # noqa: F401

EXPECTED = {
    "failure_injection_runs",
    "launch_readiness_items",
    "release_gate_results",
    "release_candidates",
}


def test_tables() -> None:
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns

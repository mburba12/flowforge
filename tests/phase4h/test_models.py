from flowforge.db.base import Base
from flowforge.phase4h import models  # noqa: F401

EXPECTED = {
    "recovery_drills",
    "integration_health_snapshots",
    "performance_test_runs",
    "audit_evidence_packages",
    "connector_alerts",
    "secret_references",
}


def test_tables() -> None:
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns

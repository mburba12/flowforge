from flowforge.db.base import Base
from flowforge.phase4c_stage6 import models  # noqa: F401


def test_tables() -> None:
    expected = {
        "workforce_connections",
        "workforce_workers",
        "workforce_jobs",
        "workforce_assignments",
        "workforce_payroll_runs",
        "workforce_payroll_lines",
        "workforce_time_entries",
        "workforce_benefit_enrollments",
        "workforce_candidates",
        "workforce_sync_runs",
        "workforce_webhook_events",
    }
    assert expected <= set(Base.metadata.tables)
    for name in expected:
        assert "tenant_id" in Base.metadata.tables[name].columns

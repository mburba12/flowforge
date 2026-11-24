from flowforge.db.base import Base
from flowforge.phase4a_stage2 import models  # noqa:F401


def test_tables() -> None:
    expected = {
        "work_schedules",
        "schedule_assignments",
        "time_entries",
        "leave_types",
        "leave_balances",
        "leave_requests",
        "pay_groups",
        "pay_periods",
    }
    assert expected <= set(Base.metadata.tables)

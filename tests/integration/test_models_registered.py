from flowforge.db.base import Base
from flowforge.integration import models  # noqa: F401


def test_phase1_tables_registered() -> None:
    expected = {
        "auth_sessions",
        "auth_invitations",
        "workflow_tasks",
        "event_outbox",
        "document_versions",
        "notification_deliveries",
        "integration_jobs",
    }

    assert expected <= set(Base.metadata.tables)

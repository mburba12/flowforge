from flowforge.db.base import Base
from flowforge.integration import models  # noqa: F401


def test_all_integrated_tables_are_tenant_scoped() -> None:
    table_names = [
        "auth_sessions",
        "auth_invitations",
        "workflow_tasks",
        "event_outbox",
        "document_versions",
        "notification_deliveries",
        "integration_jobs",
    ]

    for table_name in table_names:
        assert "tenant_id" in Base.metadata.tables[table_name].columns

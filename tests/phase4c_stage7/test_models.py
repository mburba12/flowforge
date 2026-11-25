from flowforge.db.base import Base
from flowforge.phase4c_stage7 import models  # noqa: F401


def test_tables() -> None:
    expected = {
        "engagement_connections",
        "engagement_contacts",
        "engagement_accounts",
        "engagement_leads",
        "engagement_opportunities",
        "engagement_support_tickets",
        "engagement_support_messages",
        "engagement_marketing_campaigns",
        "engagement_activities",
        "engagement_communication_events",
        "engagement_sync_runs",
        "engagement_webhook_events",
    }
    assert expected <= set(Base.metadata.tables)
    for name in expected:
        assert "tenant_id" in Base.metadata.tables[name].columns

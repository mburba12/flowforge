from flowforge.db.base import Base
from flowforge.phase5a import models  # noqa:F401

EXPECTED = {
    "phase5a_tenant_modules",
    "phase5a_onboarding_sessions",
    "phase5a_notification_deliveries",
    "phase5a_usage_meters",
    "phase5a_subscription_plans",
    "phase5a_usage_events",
    "phase5a_work_assignments",
    "phase5a_tenant_subscriptions",
    "phase5a_notifications",
    "phase5a_feature_flags",
    "phase5a_support_cases",
    "phase5a_work_items",
}


def test_models():
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns

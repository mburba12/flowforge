from flowforge.db.base import Base
from flowforge.phase5b import models  # noqa:F401

EXPECTED = {
    "phase5b_provider_registrations",
    "phase5b_incident_lockouts",
    "phase5b_security_findings",
    "phase5b_webhook_endpoints",
    "phase5b_failure_injection_runs",
    "phase5b_launch_gates",
    "phase5b_environments",
    "phase5b_execution_confirmations",
    "phase5b_capacity_runs",
    "phase5b_compliance_controls",
    "phase5b_deployment_releases",
    "phase5b_launch_decisions",
    "phase5b_pilot_tenants",
    "phase5b_webhook_deliveries",
    "phase5b_activation_gates",
    "phase5b_provider_credentials",
    "phase5b_production_actions",
    "phase5b_recovery_drills",
}


def test_models_registered():
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns

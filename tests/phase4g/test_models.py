from flowforge.db.base import Base
from flowforge.phase4g import models  # noqa: F401

EXPECTED = {
    "action_proposals",
    "action_risk_assessments",
    "phase4g_workflow_instances",
    "work_queue_items",
    "action_rollbacks",
    "workflow_steps",
    "action_proposal_items",
    "action_executions",
    "action_evidence",
    "action_approvals",
}


def test_tables() -> None:
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns

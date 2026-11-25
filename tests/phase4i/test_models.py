from flowforge.db.base import Base
from flowforge.phase4i import models  # noqa: F401

EXPECTED = {
    "connector_activation_policies",
    "writeback_results",
    "beneficiary_controls",
    "transaction_limits",
    "connector_activation_events",
    "writeback_requests",
}


def test_tables() -> None:
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns

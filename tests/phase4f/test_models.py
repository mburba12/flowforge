from flowforge.db.base import Base
from flowforge.phase4f import models  # noqa: F401

EXPECTED = {
    "ai_citations",
    "ai_evaluation_runs",
    "ai_safety_events",
    "document_extraction_fields",
    "ai_sessions",
    "ai_tool_invocations",
    "document_extractions",
    "ai_messages",
    "ai_evaluation_cases",
    "ai_usage_records",
}


def test_tables() -> None:
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns

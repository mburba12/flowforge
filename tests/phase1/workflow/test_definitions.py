import pytest

from flowforge.phase1.workflow.definitions import DefinitionsComponent


@pytest.mark.asyncio
async def test_definitions_contract() -> None:
    result = await DefinitionsComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "workflow.definitions"

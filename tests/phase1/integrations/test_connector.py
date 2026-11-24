import pytest

from flowforge.phase1.integrations.connector import ConnectorComponent


@pytest.mark.asyncio
async def test_connector_contract() -> None:
    result = await ConnectorComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "integrations.connector"

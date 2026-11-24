import pytest

from flowforge.phase1.events.publisher import PublisherComponent


@pytest.mark.asyncio
async def test_publisher_contract() -> None:
    result = await PublisherComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "events.publisher"

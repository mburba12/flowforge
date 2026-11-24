import pytest

from flowforge.phase1.analytics.aggregations import AggregationsComponent


@pytest.mark.asyncio
async def test_aggregations_contract() -> None:
    result = await AggregationsComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "analytics.aggregations"

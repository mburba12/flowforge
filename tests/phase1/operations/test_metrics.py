import pytest

from flowforge.phase1.operations.metrics import MetricsComponent


@pytest.mark.asyncio
async def test_metrics_contract() -> None:
    result = await MetricsComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "operations.metrics"

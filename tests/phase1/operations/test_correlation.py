import pytest

from flowforge.phase1.operations.correlation import CorrelationComponent


@pytest.mark.asyncio
async def test_correlation_contract() -> None:
    result = await CorrelationComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "operations.correlation"

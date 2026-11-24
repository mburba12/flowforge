import pytest

from flowforge.phase1.operations.readiness import ReadinessComponent


@pytest.mark.asyncio
async def test_readiness_contract() -> None:
    result = await ReadinessComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "operations.readiness"

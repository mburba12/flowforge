import pytest

from flowforge.phase1.operations.liveness import LivenessComponent


@pytest.mark.asyncio
async def test_liveness_contract() -> None:
    result = await LivenessComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "operations.liveness"

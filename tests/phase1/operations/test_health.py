import pytest

from flowforge.phase1.operations.health import HealthComponent


@pytest.mark.asyncio
async def test_health_contract() -> None:
    result = await HealthComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "operations.health"

import pytest

from flowforge.phase1.identity.service import ServiceComponent


@pytest.mark.asyncio
async def test_service_contract() -> None:
    result = await ServiceComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "identity.service"

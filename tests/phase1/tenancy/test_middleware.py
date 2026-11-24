import pytest

from flowforge.phase1.tenancy.middleware import MiddlewareComponent


@pytest.mark.asyncio
async def test_middleware_contract() -> None:
    result = await MiddlewareComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "tenancy.middleware"

import pytest

from flowforge.phase1.search.routes import RoutesComponent


@pytest.mark.asyncio
async def test_routes_contract() -> None:
    result = await RoutesComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "search.routes"

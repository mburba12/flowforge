import pytest

from flowforge.phase1.search.query import QueryComponent


@pytest.mark.asyncio
async def test_query_contract() -> None:
    result = await QueryComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "search.query"

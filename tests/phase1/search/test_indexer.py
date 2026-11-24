import pytest

from flowforge.phase1.search.indexer import IndexerComponent


@pytest.mark.asyncio
async def test_indexer_contract() -> None:
    result = await IndexerComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "search.indexer"

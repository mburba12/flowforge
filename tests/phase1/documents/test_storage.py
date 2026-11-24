import pytest

from flowforge.phase1.documents.storage import StorageComponent


@pytest.mark.asyncio
async def test_storage_contract() -> None:
    result = await StorageComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "documents.storage"

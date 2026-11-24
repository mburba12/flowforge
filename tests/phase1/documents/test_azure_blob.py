import pytest

from flowforge.phase1.documents.azure_blob import AzureBlobComponent


@pytest.mark.asyncio
async def test_azure_blob_contract() -> None:
    result = await AzureBlobComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "documents.azure_blob"

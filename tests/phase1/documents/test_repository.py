import pytest

from flowforge.phase1.documents.repository import RepositoryComponent


@pytest.mark.asyncio
async def test_repository_contract() -> None:
    result = await RepositoryComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "documents.repository"

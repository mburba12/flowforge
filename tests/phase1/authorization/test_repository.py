import pytest

from flowforge.phase1.authorization.repository import RepositoryComponent


@pytest.mark.asyncio
async def test_repository_contract() -> None:
    result = await RepositoryComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "authorization.repository"

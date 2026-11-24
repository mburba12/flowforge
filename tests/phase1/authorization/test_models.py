import pytest

from flowforge.phase1.authorization.models import ModelsComponent


@pytest.mark.asyncio
async def test_models_contract() -> None:
    result = await ModelsComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "authorization.models"

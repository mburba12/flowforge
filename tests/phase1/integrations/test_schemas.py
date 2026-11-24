import pytest

from flowforge.phase1.integrations.schemas import SchemasComponent


@pytest.mark.asyncio
async def test_schemas_contract() -> None:
    result = await SchemasComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "integrations.schemas"

import pytest

from flowforge.phase1.operations.errors import ErrorsComponent


@pytest.mark.asyncio
async def test_errors_contract() -> None:
    result = await ErrorsComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "operations.errors"

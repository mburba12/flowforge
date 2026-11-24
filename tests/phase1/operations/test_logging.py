import pytest

from flowforge.phase1.operations.logging import LoggingComponent


@pytest.mark.asyncio
async def test_logging_contract() -> None:
    result = await LoggingComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "operations.logging"

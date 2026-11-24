import pytest

from flowforge.phase1.tenancy.context import ContextComponent


@pytest.mark.asyncio
async def test_context_contract() -> None:
    result = await ContextComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "tenancy.context"
